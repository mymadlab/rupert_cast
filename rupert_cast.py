"""
Description: Discover and manage chromecast devices on the network
"""

import pychromecast
import zeroconf

class RupertCast:
	"""
		Description: Manage and interact with Chromecast devices on the network.
		Responsible for:
			1. Discovering Chromecast devices on the network.
			2. Retrieving device information and status.
			3. Controlling device volume and applications.
	"""
	def __init__(self):
		"""
		Initialize the RupertCast instance with the specified configuration file.
		Args:
			config_file (str): Path to the configuration file.
		"""
		self.zconf = zeroconf.Zeroconf()
		self.chromecasts = []
		self.browser = None
		self.__start_discovery()

	def get_cast_info(self, cast):
		"""
		Return best-effort cast details across pychromecast versions.
		"""
		cast_values = {
			"friendly_name": None,
			"host": None,
			"port": None,
			"uuid": None,
			"model_name": None,
			"manufacturer": None,
			"cast_type": None,
			"services": None,
		}

		cast_info = getattr(cast, "cast_info", None)
		if cast_info is not None:
			for field in ("friendly_name",
				"host",
				"port",
				"uuid",
				"model_name",
				"manufacturer",
				"cast_type"):
				cast_values[field] = getattr(cast_info, field, None)
			services = getattr(cast_info, "services", None)
			if services is not None:
				cast_values["services"] = [str(service) for service in services]

		name = getattr(cast, "name", None)
		if name and not cast_values["friendly_name"]:
			cast_values["friendly_name"] = name

		device = getattr(cast, "device", None)
		if device is not None:
			friendly_name = getattr(device, "friendly_name", None)
			if friendly_name and not cast_values["friendly_name"]:
				cast_values["friendly_name"] = friendly_name
			if cast_values["host"] is None:
				cast_values["host"] = getattr(device, "host", None)
			if cast_values["port"] is None:
				cast_values["port"] = getattr(device, "port", None)
			if cast_values["uuid"] is None:
				cast_values["uuid"] = getattr(device, "uuid", None)

		if not cast_values["friendly_name"]:
			cast_values["friendly_name"] = "Unknown device"

		return cast_values

	def get_cast_status(self, cast):
		"""
		Retrieve best-effort runtime status from a cast device.
		"""
		try:
			cast.wait(timeout=5)
		except (AttributeError, RuntimeError, OSError) as err:
			return {"available": False, "error": str(err)}

		status_obj = getattr(cast, "status", None)
		if status_obj is not None:
			status_values = {
				"available": True,
				"app_id": getattr(status_obj, "app_id", None),
				"display_name": getattr(status_obj, "display_name", None),
				"is_active_input": getattr(status_obj, "is_active_input", None),
				"is_stand_by": getattr(status_obj, "is_stand_by", None),
				"volume_level": getattr(status_obj, "volume_level", None),
				"volume_muted": getattr(status_obj, "volume_muted", None),
			}
			media_controller = getattr(cast, "media_controller", None)
			if media_controller is not None:
				media_status = getattr(media_controller, "status", None)
				if media_status is not None:
					status_values["player_state"] = getattr(media_status, "player_state", None)
			return status_values

		media_controller = getattr(cast, "media_controller", None)
		if media_controller is not None:
			media_status = getattr(media_controller, "status", None)
			if media_status is not None:
				return {
					"available": True,
					"player_state": getattr(media_status, "player_state", None),
				}

		return {"available": False, "error": "status unavailable"}

	def get_chromecasts(self):
		"""
		Discover Chromecast devices and print the status of each one.
		"""
		if not self.chromecasts:
			print("No Chromecast devices found.")
			return {}

		casts = {}

		for cast in self.chromecasts:
			info = self.get_cast_info(cast)
			casts[info.get('friendly_name', 'Unknown device')] = cast
		return casts

	def set_volume(self, cast, volume_level):
		"""
		Set the volume level of the specified cast device.
		Args:
			cast (pychromecast.Chromecast): The Chromecast device instance.
			volume_level (float): The desired volume level (0.0 to 1.0).
		"""
		if cast is not None:
			cast.set_volume(volume_level)

	def quit_app(self, cast):
		"""
		Quit the application running on the specified cast device.
		Args:
			cast (pychromecast.Chromecast): The Chromecast device instance.
		"""
		if cast is not None:
			cast.quit_app()

	def start_discovery(self):
		"""
		Start the discovery of chromecast devices on the network.
		"""
		if self.zconf is None:
			self.zconf = zeroconf.Zeroconf()
		if self.browser is not None:
			pychromecast.discovery.stop_discovery(self.browser)
		self.chromecasts, self.browser = pychromecast.get_chromecasts(zeroconf_instance=self.zconf)

	def close(self):
		"""
		Stop discovery and close Zeroconf resources.
		"""
		for cast in self.chromecasts:
			socket_client = getattr(cast, "socket_client", None)
			if socket_client is not None:
				# Prevent mDNS lookups against a closing zeroconf loop.
				setattr(socket_client, "zconf", None)

			disconnect = getattr(cast, "disconnect", None)
			if callable(disconnect):
				try:
					disconnect(timeout=2)
				except (AttributeError, OSError, RuntimeError, TimeoutError):
					pass

		if self.browser is not None:
			try:
				pychromecast.discovery.stop_discovery(self.browser)
			except (AttributeError, OSError, RuntimeError):
				pass
			self.browser = None

		self.chromecasts = []

		if self.zconf is not None:
			try:
				self.zconf.close()
			except (AttributeError, OSError, RuntimeError):
				pass
			self.zconf = None

## Private

	def __start_discovery(self):
		"""
		Start the discovery of chromecast devices on the network.
		"""
		if self.browser is not None:
			pychromecast.discovery.stop_discovery(self.browser)
		self.chromecasts, self.browser = pychromecast.get_chromecasts(zeroconf_instance=self.zconf)
