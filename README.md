# NicLink - A python interface for the Chessnut Air

# Notice
> version 0.1
> checkout this software, it solves the problem's I wannted to solve with NicLink:
    https://chromewebstore.google.com/detail/chessconnect/dmkkcjpbclkkhbdnjgcciohfbnpoaiam?hl=en-GB

## overview 

    - see the python requirements.txt for external requirements
    - only tested on gnu/linux with a chessnut air.

## Using the board on lichess with the board api
        
    In the ROOT/nic_soft/niclink_lichess dir create a dir called lichess_token.
    in this dir create a file called token. This will be a plain text file containing
    only the text of your lichess auth token.

    example:
         filename: nic_sof/niclink_lichess/token
         content: lip_5PIkq4soaF3XyFGvelx


   then cd .. and run python niclink_lichess      

## Use with gnu/linux:

    In order to use NicLink as a user in the wheel group 
    ( group can be arbitrary )
    You must give the user read and write permissions for the Chessnut air.
    This can be done through a udev rule.

    create a 99-chessnutair.rules file: /etc/udev/rules.d/99-chessnutair.rules,
    with the following:

        SUBSYSTEM=="usb", ATTRS{idVendor}:="2d80", /
        ATTRS{idProduct}:="8002", GROUP="wheel", MODE="0660"

        # set the permissions for device files
        KERNEL=="hidraw*", GROUP="wheel", MODE="0660"

    my chessnutair has the following properties, if your's differs, adjust.

        ID:  {vendor id} 2d80 : {product id} 8002

        mount poin: /dev/hidraw2

    This gives wheel group access to all of your hidraw devices,
    but wheel usualy has sudo access so they have that anyway with sudo

## have something to add/suggest?

contact me:
[nicolasvaagen@gmail.com](nicolasvaagen@gmail.com)

or, make a pull request!

# have a great day! 
