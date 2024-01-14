#include <python3.12/Python.h>
#include <pybind11/pybind11.h>
#include <pybind11/iostream.h>
#include "EasyLink.h"
#include <string>
#include <iostream>

namespace py = pybind11;

//the link to the board
shared_ptr<ChessLink> chessLink = nullptr;

//the current FEN
string currentFen;

int add(int i, int j)
{
    return i + j;
}

/**
 * Set up connection, and set up real time callback
 * @returns the created shared pointer<Chesslink>
 */
shared_ptr<ChessLink> connect()
{
    chessLink = ChessLink::fromHidConnect();

    //because, I don't know how to do async coding in two languages
    this_thread::sleep_for(chrono::seconds(2));


    if( !(chessLink -> switchUploadMode()) )
    {
        cerr << "ERROR: CAN NOT SWITCH TO UPLOAD MODE." << endl;
        throw  "ERROR: Can not connect to chessboard.";
    }

    chessLink -> connect();
    chessLink -> beep();

    //will be true on a sucess else false. Shitch to upload mode
    if( chessLink -> switchUploadMode() )
    {
        cout << "Switch upload mode a success" << endl;
        chessLink -> setRealTimeCallback(
            [](string s) {
                //keep the current fen up to date
                currentFen = s;
            });
    }
    else
    {
        cerr << "ERROR: CAN NOT SWITCH TO OUTPUT MODE." << endl;
        throw "ERROR: CAN NOT SWITCH TO OUTPUT MODE.";
    }

    chessLink -> switchRealTimeMode();
    cout << "connect out, chessboard in realtime mode" << endl;

    return chessLink;
}
/**
 * dissconect from the chessboard over usb
 */
void disconnect()
{
    if(chessLink == nullptr)
    {
        cerr << "chesslink is not connected." << endl;
        return;
    }
    //make sure we are in upload mode
    chessLink -> switchUploadMode();
    //and shut the door
    chessLink -> disconnect();    
}

/**
 * turn off all the lights on the chessboard. The chessboard will be in
 * upload mode after the function is called
 */
void lightsOut()
{
    if(chessLink == nullptr)
    {
        cerr << "chesslink is not connected." << endl;
        return;
    }

    chessLink -> switchUploadMode();

    //turn off all the lights
    chessLink -> setLed({
        bitset<8>("00000000"), //
        bitset<8>("00000000"), //
        bitset<8>("00000000"), //
        bitset<8>("00000000"), //
        bitset<8>("00000000"), //
        bitset<8>("00000000"), //
        bitset<8>("00000000"), //
        bitset<8>("00000000"), //
    });
}

/**
 * get the current fen of the board
 * @return the current fen oy the position on the board
 */
string getFEN()
{
    //if we have not connected throw error and return
    if( chessLink == nullptr )
    {
        cerr << "bChessLink is nullptr. Are you sure you are connected to board?" << endl;
        return "ERROR: no connection.";
    }
        
    //return the fen
    return currentFen;
}

/**
 * set an led on the chessboard. Will switch to upload mode
 * @param x, y: interegers in the 0 - 7 range
 * @param LEDsetting: boolean of the desired setting of the led
 */
void setLED(int x, int y, bool LEDsetting)
{
    //if we have not connected throw error and return
    if( chessLink == nullptr )
    {
        cerr << "bChessLink is nullptr. Are you sure you are connected to board?" << endl;
        return;
    }
    if(x > 7 || x < 0)
    {
        cerr << "x must be 0 - 7, x is: " << x << endl;
        return;
    }
    if(y > 7 || y < 0)
    {
        cerr << "y must be 0 - 7, y is: " << y << endl;
        return;
    }
    chessLink -> switchUploadMode();
    chessLink -> setLed((uint8_t) x, (uint8_t) y, LEDsetting);
}
/**
 * get the board to beep
*/
void beep()
{
    //if we have not connected throw error and return
    if( chessLink == nullptr )
    {
        cerr << "bChessLink is nullptr. Are you sure you are connected to board?" << endl;
        return;
    }
    //do the thing
    chessLink -> beep();
}

int main()
{
    /* connect to the board */
    connect();
    chessLink -> ChessLink::setLed((uint8_t) 4, (uint8_t) 4, true);
}

/**
 * the python bindings, for more info look up pyBind11
 * @param NickLink - Name
 * @param m - variable for our module
 */
PYBIND11_MODULE(NicLink, m)
{
    // test shit
    m.doc() = "no you";
    m.def("add", &add, py::return_value_policy::copy, "A function to add");

    // connect with a redirected out to py
    m.def("connect", []() { 
        py::scoped_ostream_redirect stream(
            std::cerr,
            py::module_::import("sys").attr("stdout")
        );
        connect();
    }, "connect to chess board device with hid even if the device is not connected,\nit will automatically connect when the device is plugged into the computer");
    
    m.def("disconnect", []() {
            py::scoped_ostream_redirect stream(
            std::cerr,
            py::module_::import("sys").attr("stdout")
        );
        disconnect();
    }, "disconnect from the chessboard.");

    // switch modes
    m.def("uploadMode", &ChessLink::switchUploadMode, py::return_value_policy::copy, "Switch to upload mode.");
    m.def("realTimeMode", &ChessLink::switchRealTimeMode, py::return_value_policy::copy, "Switch to realtime mode.");
    // doers
    m.def("setLED", &setLED, "Set a LED on the chessboard.");
    m.def("beep", &beep, "Cause the chessboard to beep.");
    // getters
    m.def("getFEN", &getFEN, py::return_value_policy::copy, "Get the FEN for the chessboard's cur position.");
}


