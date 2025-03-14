# opcua-server
This Flask + Dash + OPC UA application creates a real-time temperature monitoring dashboard. It integrates an OPC UA server to simulate and manage temperature data, while a Flask API provides secure endpoints to retrieve and update the temperature. Basic authentication ensures access control.

A background thread continuously updates the temperature every 2 seconds, storing only the last 10 readings to optimize performance. The Dash web dashboard displays the latest temperature value and an interactive real-time graph that refreshes automatically.

Users can interact with the Flask API to get the current temperature or manually update it via POST requests. Logs are maintained for monitoring system activity.

This project is ideal for industrial automation, IoT applications, and real-time data visualization, providing a robust, scalable, and secure framework for monitoring temperature changes dynamically. The system runs efficiently, combining Flask's backend with Dash's frontend for live updates. 

Flask API (Swagger Docs): http://127.0.0.1:5000/apidocs

Dash Dashboard: http://127.0.0.1:5000/dashboard/

PLC Connection string opc.tcp://127.0.0.1:4840/freeopcua/server/

Free Alternative to Matrikon OPC Explorer  
https://www.unified-automation.com/products/development-tools/uaexpert.html?gad_source=1&cHash=b272c9b8ea259f82a8f1948d3063a68b

** Next to do: to organize code structure**
