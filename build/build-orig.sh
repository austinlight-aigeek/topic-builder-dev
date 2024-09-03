#!/bin/bash

echo "Running Command --- ./build/build.sh"
echo " |"
echo " - Zipping files"

zip -r mlops-nlp-topic-builder.zip ./src/app

echo "Completed ./build/build.sh"
echo "exiting..." 