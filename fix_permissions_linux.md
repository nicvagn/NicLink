A udev rule has to be written for the chessboard see README.md and 99-chessnutair.rules.example
also see:
https://github.com/libusb/hidapi

particularly:
```
    Note that you will need to install an udev rule file with your application for
    unprivileged users to be able to access HID devices with hidapi.
    Refer to the 69-hid.rules file in the udev directory for an example.

(69-hid.rules)
# This is a sample udev file for HIDAPI devices which lets unprivileged
# users who are physically present at the system (not remote users) access
# HID devices.

# If you are using the libusb implementation of hidapi (libusb/hid.c), then
# use something like the following line, substituting the VID and PID with
# those of your device.

# HIDAPI/libusb
SUBSYSTEMS=="usb", ATTRS{idVendor}=="04d8", ATTRS{idProduct}=="003f", TAG+="uaccess"

# If you are using the hidraw implementation (linux/hid.c), then do something
# like the following, substituting the VID and PID with your device.

# HIDAPI/hidraw
KERNEL=="hidraw*", ATTRS{idVendor}=="04d8", ATTRS{idProduct}=="003f", TAG+="uaccess"

# Once done, optionally rename this file for your application, and drop it into
# /etc/udev/rules.d/.
# NOTE: these rules must have priority before 73-seat-late.rules.
# (Small discussion/explanation in systemd repo:
#  https://github.com/systemd/systemd/issues/4288#issuecomment-348166161)
# for example, name the file /etc/udev/rules.d/70-my-application-hid.rules.
# Then, re-plug your device or run:
# sudo udevadm control --reload-rules && sudo udevadm trigger

# Note that the hexadecimal values for VID and PID are case sensitive and
# must be lower case.

# TAG+="uaccess" only gives permission to physically present users, which
# is appropriate in most scenarios. If you require access to the device
# from a remote session (e.g. over SSH), add
# GROUP="plugdev", MODE="660"
# to the end of the udev rule lines, add your user to the plugdev group with:
# usermod -aG plugdev USERNAME
# then log out and log back in (or restart the system).
```
