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

    bool isValid(types::Event event);

    void incrementCollisionCount(int particleId);

private:
    std::vector<int> collisionCount;
    
    std::priority_queue<types::Event> queue;
    
};
}