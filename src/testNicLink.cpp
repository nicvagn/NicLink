#include "NicLink.cpp"
#include <iostream>


int main()
{
    connect();

    for(;;)
    {
        cout << getFEN() << "\n";
    }
}