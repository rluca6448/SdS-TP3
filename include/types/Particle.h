#pragma once

#include <string>
#include <vector>
#include <cmath>
#include <random>
#include <sstream>

namespace types {

class Particle {
public:
    Particle(int id, double x, double y, double particleRadius);
    Particle(int id, double x, double y);

    int getId() const;

    double getXLocation() const;
    void setXLocation(double x);

    double getYLocation() const;
    void setYLocation(double y);

    double getXVelocity() const;
    void setXVelocity(double xVelocity);

    double getYVelocity() const;
    void setYVelocity(double yVelocity);

    double getParticleRadius() const;

    void setMass(double mass);
    double getMass() const;

    bool getUsed() const;
    void setUsed();

    void setCellXIndex(int cellXIndex);
    int getCellXIndex() const;

    void setCellYIndex(int cellYIndex);
    int getCellYIndex() const;
    
    void advance(double dt);
    
    std::string toString() const;

    bool operator==(const Particle& other) const;

private:
    int id;

    double x;
    double y;

    double xVelocity;
    double yVelocity;

    double particleRadius;
    double mass;
    bool used;

    int cellXIndex = 0;
    int cellYIndex = 0;
    
};
}