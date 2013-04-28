"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase

import os, tempfile

from local.locations import LocationHandler

class LocationTest(TestCase):

    def test_iso_file(self):
        self._test_basic_file('ok.iso', LocationHandler.IMAGE_FILE)

    def test_video_file(self):
        self._test_basic_file('ok.avi', LocationHandler.VIDEO_FILE)

    def test_non_video_file(self):
        self._test_basic_file('ok.srt', LocationHandler.UNHANDLED_FILE)

    def test_video_files(self):
        basename, basename2='ok.avi', 'mok.mkv'
        folder = tempfile.mkdtemp()
        self._create_file(folder, basename)
        self._create_file(folder, basename2)
        results=LocationHandler(folder).iterateAllFilesInPath()
        results.sort()
        expected=[(basename, False, LocationHandler.VIDEO_FILE), (basename2, False, LocationHandler.VIDEO_FILE)]
        expected.sort()
        self.assertEqual(results, expected)

    def test_image_in_subdir(self):
        self._mtest_in_folder(('ok.iso', LocationHandler.IMAGE_FILE_ALONE_IN_DIR))

    def test_images_in_subdir(self):
        self._mtest_in_folder(('ok.iso', LocationHandler.UNHANDLED_FILE), ('nok.iso', LocationHandler.UNHANDLED_FILE))

    def test_image_subtitles_in_subdir(self):
        self._mtest_in_folder(('ok.iso', LocationHandler.IMAGE_FILE_ALONE_IN_DIR), ('nok.sub', LocationHandler.SUBTITLE_FILE_IN_DIR))

    def test_video_in_subdir(self):
        self._mtest_in_folder(('ok.mkv', LocationHandler.UNHANDLED_FILE),
            ('nok.mkv', LocationHandler.UNHANDLED_FILE),
            ('ok.srt', LocationHandler.UNHANDLED_FILE), ('ok.gif', LocationHandler.UNHANDLED_FILE))

    def test_video_in_subdir(self):
        self._mtest_in_folder(('ok.mkv', LocationHandler.VIDEO_FILE_ALONE_IN_DIR),
            ('ok.srt', LocationHandler.SUBTITLE_FILE_IN_DIR), ('ok.gif', LocationHandler.UNHANDLED_FILE))

    def test_blue_ray(self):
        expected=[]
        folder = tempfile.mkdtemp()
        loc=LocationHandler(folder)
        name='subdir'
        subfolder=os.path.join(folder,name)
        os.mkdir(subfolder)
        os.mkdir(os.path.join(subfolder,'BDMV'))
        self.assertEqual(loc.iterateAllFilesInPath(), [(name, False, LocationHandler.BLUE_RAY_FOLDER)])
        self.assertEqual(loc.getType(name), LocationHandler.BLUE_RAY_FOLDER)

    def test_blue_ray_b(self):
        expected=[]
        folder = tempfile.mkdtemp()
        loc=LocationHandler(folder)
        name='subdir'
        subfolder=os.path.join(folder,name)
        os.mkdir(subfolder)
        BDMV=os.path.join(subfolder,'BDMV')
        os.mkdir(BDMV)
        video_ts = os.path.join(subfolder,'VIDEO_TS')
        os.mkdir(video_ts)
        results=loc.iterateAllFilesInPath()
        results.sort()        
        self.assertEqual(len(results),2)
        self.assertEqual(results[0][0],name)
        self.assertIn(results[0][2],[LocationHandler.BLUE_RAY_FOLDER, LocationHandler.DVD_FOLDER])
        self.assertIn(results[1][0], [loc.getRelativeName(BDMV), loc.getRelativeName(video_ts)])
        self.assertEqual(results[1][2], LocationHandler.UNVISITED_FOLDER)
        self.assertIn(loc.getType(name), [LocationHandler.BLUE_RAY_FOLDER, LocationHandler.DVD_FOLDER])

    def test_dvd_folder_a(self):
        expected=[]
        folder = tempfile.mkdtemp()
        loc=LocationHandler(folder)
        name='subdir'
        subfolder=os.path.join(folder,name)
        os.mkdir(subfolder)
        os.mkdir(os.path.join(subfolder,'VIDEO_TS'))
        self.assertEqual(loc.iterateAllFilesInPath(), [(name, False, LocationHandler.DVD_FOLDER)])
        self.assertEqual(loc.getType(name), LocationHandler.DVD_FOLDER)

    def test_dvd_folder_b(self):
        expected=[]
        folder = tempfile.mkdtemp()
        loc=LocationHandler(folder)
        name='subdir'
        subfolder=os.path.join(folder,name)
        os.mkdir(subfolder)
        os.mkdir(os.path.join(subfolder,'VIDEO_TS'))
        os.mkdir(os.path.join(subfolder,'AUDIO_TS'))
        self.assertEqual(loc.iterateAllFilesInPath(), [(name, False, LocationHandler.DVD_FOLDER)])
        self.assertEqual(loc.getType(name), LocationHandler.DVD_FOLDER)

    def test_dvd_folder_c(self):
        expected=[]
        folder = tempfile.mkdtemp()
        loc=LocationHandler(folder)
        name='subdir'
        subfolder=os.path.join(folder,name)
        os.mkdir(subfolder)
        os.mkdir(os.path.join(subfolder,'VIDEO_TS'))
        os.mkdir(os.path.join(subfolder,'AUDIO_TS'))
        dirty=os.path.join(subfolder,'added')
        os.mkdir(dirty)
        self.assertEqual(loc.iterateAllFilesInPath(), [(name, False, LocationHandler.DVD_FOLDER),
            (loc.getRelativeName(dirty), False, LocationHandler.UNVISITED_FOLDER)])
        self.assertEqual(loc.getType(name), LocationHandler.DVD_FOLDER)

    def test_dvd_folder_d(self):
        expected=[]
        folder = tempfile.mkdtemp()
        loc=LocationHandler(folder)
        name='subdir'
        subfolder=os.path.join(folder,name)
        os.mkdir(subfolder)
        os.mkdir(os.path.join(subfolder,'VIDEO_TS'))
        os.mkdir(os.path.join(subfolder,'AUDIO_TS'))
        dirty=self._create_file(subfolder, 'dirty.mkv')
        self.assertEqual(loc.iterateAllFilesInPath(), [(name, False, LocationHandler.DVD_FOLDER),
            (loc.getRelativeName(dirty), False, LocationHandler.UNHANDLED_FILE)])
        self.assertEqual(loc.getType(name), LocationHandler.DVD_FOLDER)

    def test_dirty_direct_vobs(self):
        expected=[]
        folder = tempfile.mkdtemp()
        loc=LocationHandler(folder)
        name='subdir'
        subfolder=os.path.join(folder,name)
        os.mkdir(subfolder)
        for each in ['1.vob', '2.ifo', '3.bup']:
            self._create_file(subfolder, each)
        dirty=self._create_file(subfolder, 'kk.gif')
        self.assertEqual(loc.iterateAllFilesInPath(), [(name, False, LocationHandler.DVD_FOLDER_DIRECT),
            (loc.getRelativeName(dirty), False, LocationHandler.UNHANDLED_FILE)])
        self.assertEqual(loc.getType(name), LocationHandler.DVD_FOLDER_DIRECT)

    def test_direct_vobs(self):
        expected=[]
        folder = tempfile.mkdtemp()
        loc=LocationHandler(folder)
        name='subdir'
        subfolder=os.path.join(folder,name)
        os.mkdir(subfolder)
        for each in ['1.vob', '2.ifo', '3.bup']:
            self._create_file(subfolder, each)
        self.assertEqual(loc.iterateAllFilesInPath(), [(name, False, LocationHandler.DVD_FOLDER_DIRECT)])
        self.assertEqual(loc.getType(name), LocationHandler.DVD_FOLDER_DIRECT)



    def _create_file(self, folder, name):
        full=os.path.join(folder, name)
        with open(full, 'w') as f: pass
        return full

    def _mtest_in_folder(self, *names_expectations):
        expected=[]
        folder = tempfile.mkdtemp()
        loc=LocationHandler(folder)
        folder=os.path.join(folder,'subdir')
        os.mkdir(folder)
        for name, expectation in names_expectations:
            rname = loc.getRelativeName(self._create_file(folder, name))
            expected.append((rname, False, expectation))
        results=loc.iterateAllFilesInPath()
        results.sort()
        expected.sort()
        self.assertEqual(results, expected)        

    def _test_basic_file(self, basename, expectedType):
        folder = tempfile.mkdtemp()
        self._create_file(folder, basename)
        loc=LocationHandler(folder)
        self.assertEqual(loc.iterateAllFilesInPath(), [(basename, False, expectedType)])
        self.assertEqual(loc.getType(basename), expectedType)


