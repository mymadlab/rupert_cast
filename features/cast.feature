Feature: Manage chromecast devices

	Scenario: Discover chromecast devices
		Given I have a chromecast device available on the network
		When I initiate a discovery for chromecast devices
		Then the chromecast device should be detected
		And the device should be saved to the list of known devices
