#include "io/StateWriter.h"

namespace io {
    
void StateWriter::open(std::string path) {
    out_.open(path);

    if (!out_) {
        throw std::runtime_error("No se pudo abrir el archivo de output: " + path);
    }

    eventCounter = 0;
}

void StateWriter::writeState(std::vector<types::Particle>& particles, double time) {
    eventCounter++;

    if (eventCounter % writeEveryN != 0) {
        return; 
    }

    out_ << time << "\n";

    for (const auto& p : particles) {
        out_ << p.getXLocation() << " " << p.getYLocation() << " "
             << p.getXVelocity() << " " << p.getYVelocity() << " "
             << (p.getUsed() ? "0" : "1") << "\n"; 
    }
    out_ << "\n";
}

void StateWriter::close() {
    if (out_.is_open()) {
        out_.close();
    }
}

}