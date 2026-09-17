#pragma once

#include "types/Event.h"

#include <queue>
#include <stdexcept>
#include <vector>

namespace simulation {

class EventQueue {
public:
    explicit EventQueue(int particlesCount);

    void push(types::Event event);

    types::Event pop();

    types::Event peek();

    bool isValid(types::Event event);

    void incrementCollisionCount(int particleId);

    int getCollisionCount(int particleId) const;

private:
    std::vector<int> collisionCount;
    
    std::priority_queue<
        types::Event,
        std::vector<types::Event>,
        types::EventComparator> queue;
    
};
}