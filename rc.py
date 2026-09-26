#!/usr/bin/env python3
"""
Rupert Cast Manager
"""
import logging
import time
from rupert_cast import RupertCast


def _suppress_known_reconnect_assertion(record):
	if "Unhandled exception in worker thread, attempting reconnect" not in record.getMessage():
		return True

	exc_info = record.exc_info
	if not exc_info:
		return True

	exc_type, exc_value, _ = exc_info
	if exc_type is AssertionError and "Zeroconf instance loop must be running" in str(exc_value):
		return False

	return True


logging.getLogger("pychromecast.socket_client").addFilter(_suppress_known_reconnect_assertion)

if __name__ == '__main__': # Required to support multiprocessing in the prosumer
	rc = RupertCast()
	try:
		while True:
			try:
				casts = rc.get_chromecasts()
				if 'Living Room' in casts:
					print(rc.get_cast_info(casts['Living Room']))
					status = rc.get_cast_status(casts['Living Room'])
					print(status)
					volume_level = status.get('volume_level')
					if volume_level is not None and volume_level > 0.50:
						print(f"Volume level too high: {volume_level}")
						rc.set_volume(casts['Living Room'], 0.50)
						time.sleep(1)
						print(rc.get_cast_status(casts['Living Room']))
			except AssertionError as err:
				# Recover from pychromecast/zeroconf race during reconnect/shutdown.
				if "Zeroconf instance loop must be running" in str(err):
					print(f"Recoverable Chromecast discovery error: {err}")
					try:
						rc.close()
					except (AttributeError, OSError, RuntimeError, TimeoutError):
						pass
					time.sleep(1)
					rc = RupertCast()
				else:
					raise
			print("---")
			time.sleep(3)
	except KeyboardInterrupt:
		pass
	finally:
		rc.close()
