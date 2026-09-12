#pragma once

#include "types/Particle.h"

#include <vector>
#include <algorithm>

namespace neighbours {

class Grid {
public:
    Grid(double boardL, double boardW, int cellsX, int cellsY);

    void rebuild(std::vector<types::Particle>& particles);

    std::vector<types::Particle*> neighborsOf(const types::Particle& p) const;

private:
    double cellSizeX_;
    double cellSizeY_;

    int cellsX_;
    int cellsY_;
    
    std::vector<std::vector<types::Particle*>> grid_;

    int cellIndexX(double x) const;
    int cellIndexY(double y) const;
    int flatIndex(int cx, int cy) const { return cx + cy * cellsX_; }
    
};
}