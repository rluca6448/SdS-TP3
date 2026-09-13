#pragma once 

#include "types/Particle.h"

#include <string>
#include <vector>
#include <fstream>
#include <stdexcept>

namespace io {

class StateWriter {
public:
    void open(std::string path);

    void writeState(std::vector<types::Particle>& particles, double time);

    void close();

private:
    std::ofstream out_;
    int eventCounter = 0;
    int writeEveryN = 100;
    
};
}