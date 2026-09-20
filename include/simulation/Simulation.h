#pragma once

#include "types/Particle.h"
#include "types/Obstacle.h"
#include "types/Board.h"
#include "simulation/EventQueue.h"
#include "neighbours/Grid.h"
#include "io/StateWriter.h"

#include <vector>
#include <optional>
#include <limits>
#include <string>

#define PARTICLE_RADIUS 0.0175
#define PARTICLE_MASS 0.025
#define OBSTACLE_RADIUS 0.05

namespace simulation {

class Simulation {
public:
    Simulation(
        int particleCount = 100,
        double boardLength = 1.20,
        double boardWidth = 0.68,
        double goalpostLength = 0.20,
        double particleRadius = PARTICLE_RADIUS,
        double particleMass = PARTICLE_MASS);

    void initialize(
        const std::string& obstacleConfigPath = "generated/obstacles.txt",
        int obstacleCount = 3);

    void computeInitialCollisionTimes();

    void step();

    void run(int maxTime, io::StateWriter& writer);

    void checkGoal(types::Particle& particle);

    void recomputeCollisionsFor(types::Particle& particle);

    double getCurrentlyUsedParticlesPercentage();

    std::optional<double> getT90();
    
private: 
    bool initialized = false;

    int particleCount;
    int goalsCount;
    double currentTime;
    double particleRadius;
    double particleMass;
    std::optional<double> t90;

    std::vector<types::Particle> particles;
    std::vector<types::Obstacle> obstacles;
    types::Board board;
    neighbours::Grid grid;
    simulation::EventQueue queue;
    
    std::vector<types::Obstacle> generateObstacles(int count) const;
    std::vector<types::Particle> generateParticles(
        int count,
        double radius,
        double mass) const;
};
}