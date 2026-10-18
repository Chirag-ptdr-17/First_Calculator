# Nova Scientific Calculator

A responsive scientific calculator that runs in the browser. It uses plain HTML, CSS, and JavaScript, so it needs no build step or server.

## Features

- Scientific and hyperbolic functions, roots, powers, logarithms, factorial, gamma, and constants
- Degree and radian modes
- Black-and-white light and dark themes
- Calculation history, answer recall, and memory controls
- Keyboard input and a layout that adapts to phones and desktops
- A restricted math-expression parser; expressions are not run as JavaScript

## Run locally

Open `index.html` in a modern browser, or serve this directory with any static file server.

## Deploy to Netlify

This repository includes `netlify.toml`. In Netlify, create a new site from the GitHub repository. Use the repository root as the base directory, leave the build command empty, and set the publish directory to `.`. Netlify will publish the static files and provide a public URL. Future pushes to the connected branch will trigger new deployments.

You can also drag the project folder into Netlify's manual deploy area for a one-off deployment.
