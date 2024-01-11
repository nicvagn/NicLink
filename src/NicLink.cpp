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

//set up connection, and set up real time callback
void connect()
{
    chessLink = ChessLink::fromHidConnect();

    if( !(chessLink -> switchUploadMode()) )
    {
        cerr << "ERROR: CAN NOT SWITCH TO UPLOAD MODE." << endl;
    }

    chessLink -> connect();

    chessLink -> beep();

    //will be true on a sucess else false
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
    }

    chessLink -> switchRealTimeMode();
    this_thread::sleep_for(chrono::seconds(2));

    cout << "connect out, chessboard in realtime mode" << endl;
}

//disconnect
void disconnect()
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

    //and shut the door
    chessLink -> disconnect();    
}


//get the current fen of the board
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

//set an led on the chessboard
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



int main()
{
    /* connect to the board */
    connect();
    chessLink -> ChessLink::setLed((uint8_t) 4, (uint8_t) 4, true);
}


PYBIND11_MODULE(NicLink, m)
{
    //test shit
    m.doc() = "no you";
    m.def("add", &add, "A function to add");

    // connect with a redirected out to py
    m.def("connect", []() { 
        py::scoped_ostream_redirect stream(
            std::cerr,                                // std::ostream&
            py::module_::import("sys").attr("stdout") //python output
        );
        connect();
    }, "connect to chess board device with hid even if the device is not connected,\nit will automatically connect when the device is plugged into the computer");
    
    m.def("disconnect", []() {
            py::scoped_ostream_redirect stream(
            std::cerr,                                // std::ostream&
            py::module_::import("sys").attr("stdout") //python output
        );
        disconnect();
    }, "disconnect from the chessboard.");

    // switch modes
    m.def("uploadMode", &ChessLink::switchUploadMode, "Switch to upload mode.");
    m.def("realTimeMode", &ChessLink::switchRealTimeMode, "Switch to realtime mode.");

    // seters
    m.def("setLED", &setLED, "Set a LED on the chessboard.");
    // getters
    m.def("getFEN", &getFEN, "Get the FEN for the chessboard's cur position.");
}


