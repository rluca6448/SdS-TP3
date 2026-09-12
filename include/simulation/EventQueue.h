#pragma once

#include "types/Event.h"

#include <queue>

namespace simulation {

class EventQueue {
public:
    void push(types::Event event);

    bool isValid(types::Event event);

    void incrementCollisionCount(int particleId);

private:
    int collisionCount;

    std::priority_queue<types::Event> queue;
    
};
}