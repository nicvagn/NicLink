#include <pybind11/pybind11.h>
#include "../src/easy_link_c.h"

namespace py = pybind11;

int add(int i, int j)
{
    return i + j;
}

PYBIND11_MODULE(NicLink, m)
{
    m.doc() = "no you";

    m.def("add", &add, "A function to add");

    m.def("connect", &cl_connect, "connect to chess board device with hid even if the device is not connected,\nit will automatically connect when the device is plugged into the computer");
}