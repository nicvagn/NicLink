#include <python3.13/Python.h>
#include <pybind11/numpy.h>
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

/**
 * Set up connection, and set up real time callback
 * creates the shared_ptr<ChessLink> for use by other NicLink stuff
 */
void connect()
{
    chessLink = ChessLink::fromHidConnect();

    // if this is false, we did not connect right
    if ( !chessLink )
    {
        cerr << "ERROR: Cannot connect to chessboard" << endl;
        throw "ERROR: Cannot connect to chessboard";
    }


    // because, I don't know how to do async coding in two languages
    this_thread::sleep_for(chrono::seconds(2));

    // try to switchUploadMode, test connection
    bool successfulConnect = chessLink -> switchUploadMode();

    if( !successfulConnect )
    {
        cerr << "ERROR: CAN NOT SWITCH TO UPLOAD MODE." << endl;
        throw "ERROR: CAN NOT SWITCH TO UPLOAD MODE.";
    }

    chessLink -> connect();
    chessLink -> beep();

    cout << "Setting callback for updating currentFen." << endl;
    chessLink -> setRealTimeCallback(
          [](string s) {
              //keep the current fen up to date
              currentFen = s;
      });

    chessLink -> switchRealTimeMode();
    cout << "connect out, chessboard in realtime mode" << endl;
}

/**
 * disconnect from the chessboard over usb
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
 * set an led on the chess board.
 * @param x, y: integers in the 0 - 7 range
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

    chessLink -> setLed((uint8_t) x, (uint8_t) y, LEDsetting);
}

/**
 * set all the led's given std::string's of all the rows
 */
void setAllLEDs(const std::string rank1, const std::string rank2,
        const std::string rank3, const std::string rank4, const std::string rank5,
        const std::string rank6, const std::string rank7, const std::string rank8)
{

    chessLink -> setLed({
        bitset<8>(rank8), //
        bitset<8>(rank7), //
        bitset<8>(rank6), //
        bitset<8>(rank5), //
        bitset<8>(rank4), //
        bitset<8>(rank3), //
        bitset<8>(rank2), //
        bitset<8>(rank1), //
    });
}

/**
 * signal game over via board LED's
 */
void gameoverLights()
{
    lightsOut();
    //turn off all the lights
    chessLink -> setLed({
        bitset<8>("11111111"), //
        bitset<8>("10000001"), //
        bitset<8>("10111101"), //
        bitset<8>("10100101"), //
        bitset<8>("10100101"), //
        bitset<8>("10111101"), //
        bitset<8>("10000001"), //
        bitset<8>("11111111"), //
    });
}
/**
 * get the board to beep, switches to uploadMode and leaves the board in realTimeMode 
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

    while( true )
    {
        cout << getFEN();
        this_thread::sleep_for(chrono::seconds(2));

    }
}



/**
 * the python bindings, for more info look up pyBind11
 * @param NickLink - Name
 * @param m - variable for our module
 */
PYBIND11_MODULE(_niclink, m)
{
    m.doc() = "A passthrough between the C++ Chessnut EasyLink SDK and python";


    // connect with a redirected out to py
    /* =======================================
     * connect does not return the chess ptr, but stores it in the cpp memory. This should be called before any other functions
     * that use chess ptr.
     * ======================================*/
    m.def("connect", &connect, "connect to chess board device with hid even if the device is not connected,\nit will automatically connect when the device is plugged into the computer");
    m.def("disconnect", &disconnect, "disconnect from the chessboard.");

    // switch modes
    m.def("upload_mode", &ChessLink::switchUploadMode, py::return_value_policy::copy, "Switch to upload mode. [[ () ]]");
    m.def("realtime_mode", &ChessLink::switchRealTimeMode, py::return_value_policy::copy, "Switch to realtime mode. [[ () ]]");
    // doers
    m.def("set_led",[](int x, int y, bool LEDsetting) -> void
            {
                //release the python GIL
                py::gil_scoped_release release;
                setLED(x, y, LEDsetting);
            }, "Set a LED on the chessboard. [[ void setLED(int x, int y, bool LEDsetting)]]");
    m.def("set_all_leds", &setAllLEDs, "Set all LEDs on chessboad via str array. [[ void setAllLEDs(const std::string row8, const std::string row7, const std::string row6, const std::string row5, const std::string row4, const char row3, const std::string row2, const std::string row1)]]");
    m.def("lights_out", &lightsOut, "turn of all the lights [[ () ]]");
    m.def("gameover_lights", &gameoverLights, "show a game over lightshow. [[ () ]]"); 
    m.def("beep", &beep, "Cause the chessboard to beep. [[ () ]]");
    // getters
    m.def("get_fen", &getFEN, py::return_value_policy::copy, "Get the FEN for the chessboard's cur position. [[ () ]]");
}

