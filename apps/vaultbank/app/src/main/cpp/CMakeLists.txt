cmake_minimum_required(VERSION 3.22.1)
project("guard")

add_library(guard SHARED guard.c)

find_library(log-lib log)
target_link_libraries(guard ${log-lib})
