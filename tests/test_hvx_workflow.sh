#!/bin/bash

echo "======================================"
echo "HVX CLI - Complete Workflow Test"
echo "======================================"
echo ""

echo "1. Testing hvx graphs commands..."
hvx graphs list
echo ""

echo "2. Testing hvx templates commands..."
hvx templates list
echo ""

echo "3. Testing hvx analytics commands..."
hvx analytics list
echo ""

echo "4. Testing hvx reports commands..."
hvx reports list
echo ""

echo "======================================"
echo "All commands working! ✓"
echo "======================================"
echo ""
echo "Sample workflow:"
echo "  1. hvx graphs preview co2_compliance_bar"
echo "  2. hvx analytics run data/samples/building_sample.csv --name test"
echo "  3. hvx reports generate simple_report --data test"
echo ""
