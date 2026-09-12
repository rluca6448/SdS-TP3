#include "neighbours/Grid.h"

namespace neighbours {

Grid::Grid(double boardL, double boardW, int cellsX, int cellsY)
    : cellSizeX_(boardL / cellsX), cellSizeY_(boardW / cellsY),
      cellsX_(cellsX), cellsY_(cellsY),
      grid_(static_cast<size_t>(cellsX) * cellsY) {}

int Grid::cellIndexX(double x) const {
    return std::clamp(static_cast<int>(x / cellSizeX_), 0, cellsX_ - 1);
}

int Grid::cellIndexY(double y) const {
    return std::clamp(static_cast<int>(y / cellSizeY_), 0, cellsY_ - 1);
}

void Grid::rebuild(std::vector<types::Particle>& particles) {
    for (auto& cell : grid_) cell.clear();
    for (auto& p : particles) {
        int cx = cellIndexX(p.getXLocation());
        int cy = cellIndexY(p.getYLocation());
        p.setCellXIndex(cx);
        p.setCellYIndex(cy);
        grid_[flatIndex(cx, cy)].push_back(&p);
    }
}

std::vector<types::Particle*> Grid::neighborsOf(const types::Particle& p) const {
    std::vector<types::Particle*> result;
    int cx = p.getCellXIndex();
    int cy = p.getCellYIndex();
    for (int dx = -1; dx <= 1; dx++) {
        for (int dy = -1; dy <= 1; dy++) {
            int nx = cx + dx, ny = cy + dy;
            if (nx < 0 || nx >= cellsX_ || ny < 0 || ny >= cellsY_) continue;
            for (auto* other : grid_[flatIndex(nx, ny)]) {
                if (other->getId() != p.getId()) result.push_back(other);
            }
        }
    }
    return result;
}

} 