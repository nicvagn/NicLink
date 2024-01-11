#include <python3.12/Python.h>
#include <pybind11/pybind11.h>
//#include <pybind11/iostream.h>
#include "EasyLink.h"
#include <string>
#include <iostream>

//namespace py = pybind11;

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
        cout << "ERROR: CAN NOT SWITCH TO UPLOAD MODE." << endl;
    }

    chessLink -> connect();

    chessLink -> beep();

    //will be true on a sucess else false
    if( chessLink -> switchUploadMode() )
    {
        printf("Switch upload mode a success");
        chessLink -> setRealTimeCallback(
            [](string s) {
                //keep the current fen up to date
                currentFen = s;
                cout << s;
            });
    }
    else
    {
        printf("ERROR: CAN NOT SWITCH TO OUTPUT MODE.");
    }

    chessLink -> switchRealTimeMode();
    cout << "connect out, chessboard in realtime mode" << endl;
}

//disconnect
void disconect()
{
    

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

void testChess() {
  {
    printf("test chess entered \n");

    connect();
   
    chessLink->beep();

    chessLink->switchRealTimeMode();

    // cout << ch->getMcuVersion() << endl;

    // cout << ch->getBleVersion() << endl;

    cout << chessLink ->getBattery() << endl;

    // cout << ch->getFileCount() << endl;

    /*
    while (true) {
      auto s = ch->getFile(true);

      cout << s.size() << endl;

      if (s.size() == 0) {
        return;
      }
    }
    */


    bitset<8> ll[8] = {
        bitset<8>("10000000"), //
        bitset<8>("01000000"), //
        bitset<8>("00100000"), //
        bitset<8>("00010000"), //
        bitset<8>("00001000"), //
        bitset<8>("00000100"), //
        bitset<8>("00000010"), //
        bitset<8>("00000001"), //
    };

    int i = 0;
    while(i < 10) {
      chessLink->setLed({
          ll[i % 8],
          ll[(i + 1) % 8],
          ll[(i + 2) % 8],
          ll[(i + 3) % 8],
          ll[(i + 4) % 8],
          ll[(i + 5) % 8],
          ll[(i + 6) % 8],
          ll[(i + 7) % 8],
      });
      this_thread::sleep_for(chrono::seconds(1));
      cout << currentFen;
      i++;
    }

    chessLink->disconnect();
  }

  // unsigned char buf[] = {0x21, 0x01, 0x00};
  // auto r = ch.write(buf, sizeof(buf));

  // while (true) {
  //   unsigned char readBuf[65] = {0};
  //   auto l = ch.read(readBuf, 65);
  //   for (int i = 0; i < sizeof(readBuf); i++) {
  //     cout << hex << " " << int(readBuf[i]);
  //   }
  //   cout << endl;
  //   cout << l << endl;
  // }

  // cout << ch->switchRealTimeMode() << endl;
}

//get the current fen of the board
string getFEN()
{
    //if we have not connected throw error and return
    if( chessLink == nullptr )
    {
        fprintf(stderr, "bChessLink is nullptr. Are you sure you are connected to board?");
        return "ERROR: no connection.";
    }
        
    //return the fen
    return currentFen;
}


int main()
{
    /* connect to the board */
    connect();
}


PYBIND11_MODULE(NicLink, m)
{
    //test shit
    m.doc() = "no you";
    m.def("add", &add, "A function to add");

    // connect with a redirected out to py
    m.def("connect", []() { 
        py::scoped_ostream_redirect stream(
            std::cout,                                // std::ostream&
            py::module_::import("sys").attr("stdout") //python output
        );
        connect();
    }, "connect to chess board device with hid even if the device is not connected,\nit will automatically connect when the device is plugged into the computer");
    
    m.def("disconnect", &disconect, "Disconect from the chessboard.");

    m.def("uploadMode", &ChessLink::switchUploadMode, "Switch to upload mode.");
    m.def("realTimeMode", &ChessLink::switchRealTimeMode, "Switch to realtime mode.");

    m.def("testChess", &testChess, "test chess");
}
