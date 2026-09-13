#pragma once

#include "types/Particle.h"
#include "types/Obstacle.h"
#include "types/Board.h"
#include "simulation/EventQueue.h"
#include "neighbours/Grid.h"

#include <vector>
#include <optional>

namespace simulation {

class Simulation {
public:
    void initialize();

    void computeInitialCollisionTimes();

    void step();

    void run(int maxTime);

    void checkGoal(types::Particle& particle);

    void recomputeCollisionsFor(types::Particle& particle);

    double getCurrentlyUsedParticlesPercentage();

    std::optional<double> getT90();
    
private: 
    int particleCount;
    int currentTime;
    int goalsCount;

    std::vector<types::Particle*> particles;
    std::vector<types::Obstacle*> obstacles;
    types::Board board;
    neighbours::Grid grid;
    simulation::EventQueue queue;
    
};
}