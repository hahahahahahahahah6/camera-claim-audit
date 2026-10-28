"""Spec cases 01–35. Added phrase-exhaustion coverage:
test_phrase_camera_00 covers: captures photos from your camera
test_phrase_camera_01 covers: capture photos from your camera
test_phrase_camera_02 covers: captures images from your camera
test_phrase_camera_03 covers: capture images from your camera
test_phrase_camera_04 covers: takes photos with your camera
test_phrase_camera_05 covers: take photos with your camera
test_phrase_camera_06 covers: takes pictures with your camera
test_phrase_camera_07 covers: take pictures with your camera
test_phrase_camera_08 covers: captures video from your camera
test_phrase_camera_09 covers: capture video from your camera
test_phrase_camera_10 covers: records video from your camera
test_phrase_camera_11 covers: record video from your camera
test_phrase_camera_12 covers: captures webcam video
test_phrase_camera_13 covers: capture webcam video
test_phrase_camera_14 covers: captures webcam images
test_phrase_camera_15 covers: capture webcam images
test_phrase_camera_16 covers: takes webcam photos
test_phrase_camera_17 covers: take webcam photos
test_phrase_camera_18 covers: supports camera capture
test_phrase_camera_19 covers: camera capture support
test_phrase_camera_20 covers: camera photo capture
test_phrase_camera_21 covers: camera video capture
test_phrase_camera_22 covers: webcam capture support
test_phrase_camera_23 covers: supports webcam capture
test_phrase_camera_24 covers: camera input support
test_phrase_camera_25 covers: uses your camera to capture
test_phrase_camera_26 covers: captures from your camera
test_phrase_camera_27 covers: capture from your camera
test_phrase_camera_28 covers: records from your camera
test_phrase_camera_29 covers: record from your camera
test_phrase_nocamera_00 covers: does not capture photos from your camera
test_phrase_nocamera_01 covers: does not capture images from your camera
test_phrase_nocamera_02 covers: does not take photos with your camera
test_phrase_nocamera_03 covers: does not capture video from your camera
test_phrase_nocamera_04 covers: does not record video from your camera
test_phrase_nocamera_05 covers: does not capture from your camera
test_phrase_nocamera_06 covers: does not record from your camera
test_phrase_nocamera_07 covers: does not use your camera
test_phrase_nocamera_08 covers: does not access your camera
test_phrase_nocamera_09 covers: camera capture not supported
test_phrase_nocamera_10 covers: webcam capture not supported
test_phrase_nocamera_11 covers: camera input not supported
test_phrase_nocamera_12 covers: no camera capture
test_phrase_nocamera_13 covers: no webcam capture
test_phrase_nocamera_14 covers: without camera capture
test_phrase_nocamera_15 covers: without webcam capture
test_phrase_nocamera_16 covers: no camera input
test_phrase_nocamera_17 covers: no camera access
"""
import contextlib
import io
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from camera_claim_audit.audit import audit, claims, evidence
from camera_claim_audit.__main__ import main
from camera_claim_audit.phrases import CAMERA, NOCAMERA

ROOT = Path(__file__).resolve().parents[1]
GOOD = 'import cv2\ncap = cv2.VideoCapture(0)\ncap.read()'
CLAIM = CAMERA[0]

class AuditTests(unittest.TestCase):
    def project(self, source=None, doc=CLAIM, path='app.py'):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root/'README.md').write_text(doc)
        if source is not None:
            target = root/path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source)
        return root

    def run_cli(self, root, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main([str(root), '--json', *args])
        return code, json.loads(out.getvalue())

    def check(self, source=None, doc=CLAIM, expected='HIGH', path='app.py'):
        root = self.project(source, doc, path)
        code, result = self.run_cli(root)
        self.assertEqual(result['findings'], [] if expected is None else [dict(rule='documented-no-camera-claim-false' if doc in NOCAMERA else 'documented-camera-claim-false', severity=expected, message='Documented absence conflicts with production capture evidence.' if doc in NOCAMERA else 'Documented device intake lacks production capture evidence.')])
        self.assertEqual(code, 2 if expected == 'HIGH' else 0)
        return root

    def test_01_plain(self): self.check(GOOD, expected=None)
    def test_02_alias(self): self.check('import cv2 as cv\ncap=cv.VideoCapture(0)\ncap.read()', expected=None)
    def test_03_from(self): self.check('from cv2 import VideoCapture\ncap=VideoCapture(0)\ncap.read()', expected=None)
    def test_04_self(self): self.check('import cv2\nself.cap=cv2.VideoCapture(0)\nself.cap.read()', expected=None)
    def test_05_chain(self): self.check('import cv2\ncv2.VideoCapture(0).read()', expected=None)
    def test_06_constant(self): self.check(GOOD.replace('(0)', '(CAMERA_INDEX)'), expected=None)
    def test_07_pi2(self): self.check('from picamera2 import Picamera2\ncam=Picamera2()\ncam.capture_file("x")', expected=None)
    def test_08_pi2_chain(self): self.check('from picamera2 import Picamera2\nPicamera2().capture_array()', expected=None)
    def test_09_pi2_self(self): self.check('from picamera2 import Picamera2\nself.cam=Picamera2()\nself.cam.capture_image()', expected=None)
    def test_10_legacy(self): self.check('from picamera import PiCamera\ncam=PiCamera()\ncam.capture("x")', expected=None)
    def test_11_record(self): self.check('from picamera import PiCamera\ncam=PiCamera()\ncam.start_recording("x")', expected=None)
    def test_12_import(self): self.check('import cv2')
    def test_13_string(self): self.check('word="camera"')
    def test_14_object(self): self.check('import cv2\ncap=cv2.VideoCapture(0)')
    def test_15_pi2_object(self): self.check('from picamera2 import Picamera2\ncam=Picamera2()')
    def test_16_unbound_read(self): self.check('cap.read()')
    def test_17_unbound_capture(self): self.check('cam.capture_file("x")')
    def test_18_file(self): self.check(GOOD.replace('(0)', '("video.mp4")'))
    def test_19_load(self): self.check('import cv2\nfrom PIL import Image\ncv2.imread("x")\nImage.open("x")')
    def test_20_screen(self): self.check('import pyautogui\npyautogui.screenshot()')
    def test_21_display(self): self.check('import cv2\ncv2.imshow("x", frame)\ncv2.imwrite("x", frame)')
    def test_22_negative(self): self.check(GOOD, 'no camera capture')
    def test_23_no_claim(self): self.check(GOOD, 'A useful tool.', None)
    def test_24_noun(self): self.check('import cv2', 'the camera chapter explains delivery', None)
    def test_25_user(self): self.check('import cv2', 'point your camera at the scene before starting', None)
    def test_26_screenshot(self): self.check('pyautogui.screenshot()', 'takes screenshots', None)
    def test_27_no_source(self):
        self.check()
        self.check(None, 'no camera capture', None)
    def test_28_tests_only(self):
        root = self.check(GOOD, expected='MEDIUM', path='tests/test_device.py')
        self.assertEqual(self.run_cli(root, '--fail-on', 'MEDIUM')[0], 2)
    def test_29_fences_inline(self):
        self.check(None, '```text\n'+CLAIM+'\n```', None)
        self.check(None, '`'+CLAIM+'`')
    def test_30_negation(self): self.assertEqual(claims('does not capture photos from your camera'), (False, True))
    def test_31_self(self):
        result = audit(ROOT)
        self.assertEqual(result['findings'], [])
        self.assertEqual(result['claims'], {'camera': False, 'no_camera': False})
        self.assertEqual(claims((ROOT/'README.md').read_text()), (False, False))
        text = (ROOT/'README.md').read_text().lower().replace('-', ' ')
        self.assertFalse(any(p in text for p in CAMERA+NOCAMERA))
    def test_32_cli(self):
        out=io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as exc: main(['--version'])
        self.assertEqual(exc.exception.code, 0)
        self.assertEqual(out.getvalue().strip(), '0.1.0')
        root=self.project(GOOD, 'Overview')
        (root/'docs').mkdir()
        (root/'docs/claim.md').write_text('no camera capture')
        self.assertEqual(self.run_cli(root)[0], 2)
        self.assertEqual(self.run_cli(root, '--ignore', 'docs/*')[0], 0)
        out=io.StringIO()
        with contextlib.redirect_stdout(out): self.assertEqual(main([str(root), '--verbose', '--ignore', 'docs/*']), 0)
        self.assertIn('app.py', out.getvalue())
        with contextlib.redirect_stderr(io.StringIO()): self.assertEqual(main([str(root/'missing')]), 1)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc: main([])
        self.assertEqual(exc.exception.code, 1)
    def test_33_env(self):
        original = Path.read_text
        def guarded(path, *args, **kwargs):
            self.assertNotEqual(path.name, '.env')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', guarded): audit(ROOT)
    def test_34_packaging(self):
        for path in list((ROOT/'camera_claim_audit').glob('*.py')) + list((ROOT/'tests').glob('*.py')) + [ROOT/'README.md']:
            self.assertIsNone(re.search(r'\b' + 'py' + r'thon\b', path.read_text()))
        config=(ROOT/'pyproject.toml').read_text()
        self.assertIn('setuptools>=77', config)
        self.assertIn('license = "MIT"', config)
        self.assertIn('recursive-include tests', (ROOT/'MANIFEST.in').read_text())
    def test_35_phrase_inventory(self):
        self.assertEqual(len(CAMERA), 30)
        self.assertEqual(len(NOCAMERA), 18)

    def test_phrase_camera_00(self):
        self.check(None, 'captures photos from your camera')
    def test_phrase_camera_01(self):
        self.check(None, 'capture photos from your camera')
    def test_phrase_camera_02(self):
        self.check(None, 'captures images from your camera')
    def test_phrase_camera_03(self):
        self.check(None, 'capture images from your camera')
    def test_phrase_camera_04(self):
        self.check(None, 'takes photos with your camera')
    def test_phrase_camera_05(self):
        self.check(None, 'take photos with your camera')
    def test_phrase_camera_06(self):
        self.check(None, 'takes pictures with your camera')
    def test_phrase_camera_07(self):
        self.check(None, 'take pictures with your camera')
    def test_phrase_camera_08(self):
        self.check(None, 'captures video from your camera')
    def test_phrase_camera_09(self):
        self.check(None, 'capture video from your camera')
    def test_phrase_camera_10(self):
        self.check(None, 'records video from your camera')
    def test_phrase_camera_11(self):
        self.check(None, 'record video from your camera')
    def test_phrase_camera_12(self):
        self.check(None, 'captures webcam video')
    def test_phrase_camera_13(self):
        self.check(None, 'capture webcam video')
    def test_phrase_camera_14(self):
        self.check(None, 'captures webcam images')
    def test_phrase_camera_15(self):
        self.check(None, 'capture webcam images')
    def test_phrase_camera_16(self):
        self.check(None, 'takes webcam photos')
    def test_phrase_camera_17(self):
        self.check(None, 'take webcam photos')
    def test_phrase_camera_18(self):
        self.check(None, 'supports camera capture')
    def test_phrase_camera_19(self):
        self.check(None, 'camera capture support')
    def test_phrase_camera_20(self):
        self.check(None, 'camera photo capture')
    def test_phrase_camera_21(self):
        self.check(None, 'camera video capture')
    def test_phrase_camera_22(self):
        self.check(None, 'webcam capture support')
    def test_phrase_camera_23(self):
        self.check(None, 'supports webcam capture')
    def test_phrase_camera_24(self):
        self.check(None, 'camera input support')
    def test_phrase_camera_25(self):
        self.check(None, 'uses your camera to capture')
    def test_phrase_camera_26(self):
        self.check(None, 'captures from your camera')
    def test_phrase_camera_27(self):
        self.check(None, 'capture from your camera')
    def test_phrase_camera_28(self):
        self.check(None, 'records from your camera')
    def test_phrase_camera_29(self):
        self.check(None, 'record from your camera')
    def test_phrase_nocamera_00(self):
        self.assertEqual(claims('does not capture photos from your camera'), (False, True))
        self.check(GOOD, 'does not capture photos from your camera')
        self.check(None, 'does not capture photos from your camera', None)
    def test_phrase_nocamera_01(self):
        self.assertEqual(claims('does not capture images from your camera'), (False, True))
        self.check(GOOD, 'does not capture images from your camera')
        self.check(None, 'does not capture images from your camera', None)
    def test_phrase_nocamera_02(self):
        self.assertEqual(claims('does not take photos with your camera'), (False, True))
        self.check(GOOD, 'does not take photos with your camera')
        self.check(None, 'does not take photos with your camera', None)
    def test_phrase_nocamera_03(self):
        self.assertEqual(claims('does not capture video from your camera'), (False, True))
        self.check(GOOD, 'does not capture video from your camera')
        self.check(None, 'does not capture video from your camera', None)
    def test_phrase_nocamera_04(self):
        self.assertEqual(claims('does not record video from your camera'), (False, True))
        self.check(GOOD, 'does not record video from your camera')
        self.check(None, 'does not record video from your camera', None)
    def test_phrase_nocamera_05(self):
        self.assertEqual(claims('does not capture from your camera'), (False, True))
        self.check(GOOD, 'does not capture from your camera')
        self.check(None, 'does not capture from your camera', None)
    def test_phrase_nocamera_06(self):
        self.assertEqual(claims('does not record from your camera'), (False, True))
        self.check(GOOD, 'does not record from your camera')
        self.check(None, 'does not record from your camera', None)
    def test_phrase_nocamera_07(self):
        self.assertEqual(claims('does not use your camera'), (False, True))
        self.check(GOOD, 'does not use your camera')
        self.check(None, 'does not use your camera', None)
    def test_phrase_nocamera_08(self):
        self.assertEqual(claims('does not access your camera'), (False, True))
        self.check(GOOD, 'does not access your camera')
        self.check(None, 'does not access your camera', None)
    def test_phrase_nocamera_09(self):
        self.assertEqual(claims('camera capture not supported'), (False, True))
        self.check(GOOD, 'camera capture not supported')
        self.check(None, 'camera capture not supported', None)
    def test_phrase_nocamera_10(self):
        self.assertEqual(claims('webcam capture not supported'), (False, True))
        self.check(GOOD, 'webcam capture not supported')
        self.check(None, 'webcam capture not supported', None)
    def test_phrase_nocamera_11(self):
        self.assertEqual(claims('camera input not supported'), (False, True))
        self.check(GOOD, 'camera input not supported')
        self.check(None, 'camera input not supported', None)
    def test_phrase_nocamera_12(self):
        self.assertEqual(claims('no camera capture'), (False, True))
        self.check(GOOD, 'no camera capture')
        self.check(None, 'no camera capture', None)
    def test_phrase_nocamera_13(self):
        self.assertEqual(claims('no webcam capture'), (False, True))
        self.check(GOOD, 'no webcam capture')
        self.check(None, 'no webcam capture', None)
    def test_phrase_nocamera_14(self):
        self.assertEqual(claims('without camera capture'), (False, True))
        self.check(GOOD, 'without camera capture')
        self.check(None, 'without camera capture', None)
    def test_phrase_nocamera_15(self):
        self.assertEqual(claims('without webcam capture'), (False, True))
        self.check(GOOD, 'without webcam capture')
        self.check(None, 'without webcam capture', None)
    def test_phrase_nocamera_16(self):
        self.assertEqual(claims('no camera input'), (False, True))
        self.check(GOOD, 'no camera input')
        self.check(None, 'no camera input', None)
    def test_phrase_nocamera_17(self):
        self.assertEqual(claims('no camera access'), (False, True))
        self.check(GOOD, 'no camera access')
        self.check(None, 'no camera access', None)

    def test_provider_matrix(self):
        for provider, constructor, methods in [('cv2','VideoCapture',['read']), ('picamera2','Picamera2',['capture_file','capture_array','capture_image','capture_buffer','capture_metadata']), ('picamera','PiCamera',['capture','start_recording'])]:
            for method in methods:
                for source in [f'import {provider} as p\np.{constructor}().{method}()', f'from {provider}.device import {constructor} as C\nc=C()\nc.{method}()', f'import {provider}\nself.c={provider}.{constructor}()\nself.c.{method}()']:
                    with self.subTest(source=source): self.assertTrue(evidence(source))
        self.assertFalse(evidence('from picamera2 import PiCamera\nPiCamera().capture()'))
        self.assertFalse(evidence('from picamera import Picamera2\nPicamera2().capture_file()'))

    def test_explicit_non_evidence(self):
        for source in ['input("device")', 'from picamera import PiCamera\nc=PiCamera()', 'c.capture()', 'import imageio\nimageio.imread("x")', 'import mss\nmss.mss().grab({})', 'import cv2\ncv2.CascadeClassifier().detectMultiScale(cv2.imread("x"))', 'def capture():\n print("camera")\n return 1', '@app.get("/capture")\ndef route():\n return "camera"', 'import subprocess\nsubprocess.run(["fswebcam"])', '"""import cv2; cv2.VideoCapture(0).read()"""', '# import cv2; cv2.VideoCapture(0).read()']:
            with self.subTest(source=source): self.assertFalse(evidence(source))

    def test_normalization_boundaries_and_paragraphs(self):
        self.assertEqual(claims("SUPPORTS-CAMERA\nCAPTURE"), (True, False))
        self.assertEqual(claims("doesn't capture photos from your camera"), (False, True))
        self.assertEqual(claims('supports camera\n\ncapture'), (False, False))
        self.assertEqual(claims('xsupports camera capturex'), (False, False))
        self.assertEqual(claims('~~~md\n'+CLAIM+'\n~~~'), (False, False))

    def test_scope_symlinks_and_two_families(self):
        for path in ['tests/a.py', 'test_a.py', 'a_test.py']:
            root=self.project(GOOD, path=path)
            self.assertEqual(audit(root)['findings'][0]['severity'], 'MEDIUM')
        for path in ['fixtures/a.py', 'docs/a.py', 'examples/a.py']:
            root=self.project(GOOD, path=path)
            self.assertEqual(audit(root)['findings'][0]['severity'], 'HIGH')
        root=self.project(GOOD, path='external.py')
        (root/'external.py').unlink()
        (root/'external.py').symlink_to(ROOT/'tests/fixtures/good/app.py')
        self.assertEqual(audit(root)['findings'][0]['severity'], 'HIGH')
        root=self.project(None, CLAIM+'\n\nno camera capture')
        self.assertEqual(len(audit(root)['findings']), 1)
        (root/'app.py').write_text(GOOD)
        result=audit(root)
        self.assertEqual(len(result['findings']), 1)
        self.assertEqual(result['findings'][0]['rule'], 'documented-no-camera-claim-false')
        root=self.project(GOOD, 'Overview')
        (root/'tests/docs').mkdir(parents=True)
        (root/'tests/docs/negative.md').write_text('no camera capture')
        self.assertEqual(audit(root)['findings'][0]['severity'], 'HIGH')
