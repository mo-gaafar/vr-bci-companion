# html_content = """
#     <!DOCTYPE html>
#     <html>
#     <head>
#     <title>BCI Control Panel</title>
#     <link rel='stylesheet' href='https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css'>
#     <script src='https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js'></script>
#     <script src='https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.16.0/umd/popper.min.js'></script>
#     <script src='https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js'></script>

#     <style>
#       body {
#         font-family: sans-serif;
#         margin: 20px;
#       }

#       h1, h2 {
#         color: #336699; /* A shade of blue */
#       }

#       button {
#           background-color: #4CAF50; /* Example: Green background */
#           color: white;
#           padding: 12px 20px;
#           margin: 8px 0;
#           border: none;
#           border-radius: 4px;   /* Slightly rounded corners */
#           cursor: pointer;
#           transition: background-color 0.3s ease; /* Add a transition effect */
#       }

#       button:hover {
#           background-color: #45a049; /* Slightly darker green on hover */
#       }
#     </style>

#     </head>
#     <body>

#     <div class="container">
#       <h1>BCI Control Panel</h1>
#       <p>Welcome to the control panel for your Brain-Computer Interface (BCI) system.</p>

#       <div>
#         <h2>Status</h2>
#         <p><strong>Connection Status:</strong> <span id="connection-status">Disconnected</span></p>
#         <p><strong>Signal Quality:</strong> <span id="signal-quality"> - </span></p>
#       </div>

#       <div>
#         <h2>Configuration</h2>
#         <ul>
#           <li><button href="configure-bci">Configure BCI Connection</button></li>
#           <li><button href="calibrate">Calibrate BCI</button> (Placeholder)</li>
#         </ul>
#       </div>

#       <div>
#         <h2>API Documentation</h2>
#         <ul>
#           <li><a href="/docs">Swagger UI</a></li>
#           <li><a href="/redoc">ReDoc</a></li>
#         </ul>
#       </div>
#     </div>

#     </body>
#     </html>
#     """


html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Backend Server Home</title>
  <link rel="icon" type="image/x-icon" href="favicon.ico">  
  <style>
    body {
      font-family: sans-serif;
      margin: 20px;
      }

      h1, h2 {
        color: #336699; /* A shade of blue */
      }

      button {
          background-color: #4CAF50; /* Example: Green background */
          color: white;
          padding: 12px 20px;
          margin: 8px 0;
          border: none;
          border-radius: 4px;   /* Slightly rounded corners */
          cursor: pointer;
          transition: background-color 0.3s ease; /* Add a transition effect */
      }

      button:hover {
          background-color: #45a049; /* Slightly darker green on hover */
      }
    

    h1 {
      text-align: left;
      font-size: 2em; /* Example font size */
    }

    .button-container {
      display: flex;
      align-items: center;
      margin-top: 20px;
    }

    .documentation-button { 
      background-color: green; /* Green background */
      color: white;
      padding: 10px 20px;
      text-decoration: none;
      border: none; 
      border-radius: 5px; 
      cursor: pointer;  
      margin-right: 10px;  /* Add space between buttons */
    }
  </style>
</head>
<body>
  <h1 style="text-align: left;">Backend Server Home</h1>

  <p>This web interface provides administrative functionalities for managing various aspects of a backend server system, including:</p>
  <ul>
    <li>Patient Database: Manage patient data...</li>
    <li>Machine Learning: Manage machine learning models...</li>
    <li>Server Status: Monitor the health and performance...</li>
  </ul>

  <div class="button-container">
    <a href="/docs" class="documentation-button">API Documentation</a>
    <a href="/redoc" class="documentation-button">ReDoc</a>
  </div>

  </body>
</html>

"""


# **Breakdown**

# *   **Documentation Buttons:**  Links to your API documentation and ReDoc.
# *   **Functionality Sections:** Represents patient database and machine learning areas with placeholder links.
# *   **Status Indicators:**  Placeholders for displaying real-time status updates.

# **Key Considerations**

# *   **Dynamic Updates:**  The status indicator placeholders will likely need to be updated dynamically using JavaScript or server-side logic.
# *   **Framework Integration:**  If you are using a specific Python backend framework, you'll need to integrate this HTML  string into your framework's templating system.

# **Next Steps: Let's Add Depth**

# 1.  **Real Status Logic:**  Do you want assistance outlining how to implement the logic to fetch and display real-time status information in the placeholders?
# 2.  **Additional Features:** Are there other features or sections you'd like to include on this home page?
