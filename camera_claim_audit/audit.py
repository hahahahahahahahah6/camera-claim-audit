"""Offline AST inspection. Audited source is never executed."""
import ast
import fnmatch
import re
from pathlib import Path
from .phrases import CAMERA, NOCAMERA


def normalize(text):
    return re.sub(r'\s+', ' ', text.lower().replace("n't", ' not').replace('-', ' ')).strip()


def claims(text):
    lines = []
    fence = None
    for line in text.splitlines():
        marker = re.match(r'^\s{0,3}(`{3,}|~{3,})', line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            lines.append('')
        elif fence is None:
            lines.append(line)
    positive = negative = False
    for paragraph in re.split(r'\n\s*\n', '\n'.join(lines)):
        paragraph = normalize(paragraph)
        for phrase in sorted(NOCAMERA, key=len, reverse=True):
            paragraph, count = re.subn(r'\b' + re.escape(phrase) + r'\b', ' ', paragraph)
            negative |= bool(count)
        positive |= any(re.search(r'\b' + re.escape(p) + r'\b', paragraph) for p in CAMERA)
    return positive, negative


def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted(node.value)
        return base + '.' + node.attr if base else ''
    return ''


def evidence(source):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    aliases = {}
    providers = ('cv2', 'picamera2', 'picamera')
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                if item.name.split('.')[0] in providers:
                    aliases[item.asname or item.name.split('.')[0]] = item.name if item.asname else item.name.split('.')[0]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            if node.module.split('.')[0] in providers:
                for item in node.names:
                    aliases[item.asname or item.name] = node.module + '.' + item.name

    def creation(node):
        if not isinstance(node, ast.Call):
            return None
        path = dotted(node.func).split('.')
        resolved = aliases.get(path[0], '')
        if not resolved:
            return None
        path = (resolved + ('.' + '.'.join(path[1:]) if len(path) > 1 else '')).split('.')
        provider, name = path[0], path[-1]
        if provider == 'cv2' and name == 'VideoCapture':
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                return None
            return provider
        if (provider, name) in {('picamera2', 'Picamera2'), ('picamera', 'PiCamera')}:
            return provider
        return None

    bindings = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            provider = creation(node.value)
            for target in node.targets:
                key = dotted(target)
                if isinstance(target, ast.Name) or (isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self'):
                    if provider:
                        bindings[key] = provider
    methods = {'cv2': {'read'}, 'picamera2': {'capture_file', 'capture_array', 'capture_image', 'capture_buffer', 'capture_metadata'}, 'picamera': {'capture', 'start_recording'}}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            provider = creation(node.func.value) or bindings.get(dotted(node.func.value))
            if provider and node.func.attr in methods[provider]:
                return True
    return False


def audit(root, ignores=()):
    root = Path(root)
    if not root.is_dir() or not root.stat().st_mode & 0o444 or not root.stat().st_mode & 0o111:
        raise ValueError('Root must be a readable directory')
    positive = negative = False
    production, testing = [], []
    excluded = {'fixtures', 'docs', 'examples'}
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents if parent != root) or not path.is_file():
            continue
        if any(fnmatch.fnmatch(relative.as_posix(), pattern) for pattern in ignores):
            continue
        if path.suffix.lower() == '.md' and (relative.as_posix() == 'README.md' or 'docs' in relative.parts[:-1]):
            pos, neg = claims(path.read_text(encoding='utf-8'))
            positive |= pos
            negative |= neg
        if path.suffix != '.py' or excluded.intersection(relative.parts[:-1]):
            continue
        test = 'tests' in relative.parts[:-1] or path.name.startswith('test_') or path.name.endswith('_test.py')
        if evidence(path.read_text(encoding='utf-8')):
            (testing if test else production).append(relative.as_posix())
    findings = []
    if positive and not production:
        findings.append({'rule': 'documented-camera-claim-false', 'severity': 'MEDIUM' if testing else 'HIGH', 'message': 'Documented device intake lacks production capture evidence.'})
    if negative and production:
        findings.append({'rule': 'documented-no-camera-claim-false', 'severity': 'HIGH', 'message': 'Documented absence conflicts with production capture evidence.'})
    return {'findings': findings, 'evidence': production, 'test_evidence': testing, 'claims': {'camera': positive, 'no_camera': negative}}
