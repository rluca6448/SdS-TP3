#pragma once 

#include "types/Particle.h"

#include <string>
#include <vector>
#include <fstream>

namespace io {

class StateWriter {
public:
    void open(std::string parh);

    void writeState(std::vector<types::Particle>& particles, double time);

    void close();

private:
    std::ofstream out_;
    int eventCounter;
    
};
}