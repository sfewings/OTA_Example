# OTA_Example
Testing for Pyboard over the air updating from a GIT repo. 
See https://github.com/rdehuyss/micropython-ota-updater

1. Create a directory "main" on the Pyboard
2. Go to the Git hub repo https://github.com/sfewings/OTA_Example
3. Set a release tag with a number greater than already released e.g. 1.2
4. run the code on the Pyboard and go to the http:\\ip\index
5. Call "Check for updates". This should create a folder /next with a file called .version_on_reboot containing the updated release on GitHub
6. Call "Install updates, if available". This will
	a) download the latest file set in https://github.com/sfewings/OTA_Example/tree/master/main to next directory. 
	b) rename the file .version_on_reboot to .version (the new version on the pyboard
	c) delete any folder called OTABackup
	d) copy the folder main to OTABackup
	e) rename the folder next to main
	f) reset the pyboard to restart

That's it!