#!/bin/bash
# Test script for county_data API
# Attribution: Created with AI assistance (Cascade)

API_URL="${1:-http://localhost:8000}"

echo "Testing County Health Data API at: $API_URL"
echo "=========================================="
echo ""

echo "Test 1: Valid request (ZIP 02138, Adult obesity)"
echo "Expected: 200 OK with JSON array"
curl -X POST "$API_URL/county_data" \
  -H "Content-Type: application/json" \
  -d '{"zip": "02138", "measure_name": "Adult obesity"}' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | head -c 500
echo ""
echo ""

echo "Test 2: Easter egg (coffee=teapot)"
echo "Expected: 418 I'm a teapot"
curl -X POST "$API_URL/county_data" \
  -H "Content-Type: application/json" \
  -d '{"coffee": "teapot"}' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s
echo ""

echo "Test 3: Missing parameters"
echo "Expected: 400 Bad Request"
curl -X POST "$API_URL/county_data" \
  -H "Content-Type: application/json" \
  -d '{}' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s
echo ""

echo "Test 4: Invalid ZIP code"
echo "Expected: 404 Not Found"
curl -X POST "$API_URL/county_data" \
  -H "Content-Type: application/json" \
  -d '{"zip": "99999", "measure_name": "Adult obesity"}' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s
echo ""

echo "Test 5: Invalid endpoint"
echo "Expected: 404 Not Found"
curl -X POST "$API_URL/invalid_endpoint" \
  -H "Content-Type: application/json" \
  -d '{"zip": "02138", "measure_name": "Adult obesity"}' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s
echo ""

echo "=========================================="
echo "All tests completed!"
