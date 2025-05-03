let nodes = [];
let points = [];
let stages = ['Nodes', 'Block 1', 'Vote 1', 'Block 2', 'Vote 2', 'Election'];
let stageWidth;
let totalSteps = 120; // Number of frames to complete one stage, doubled for slower propagation
let traits = [];
let restartTime = 10000; // 10 seconds
let simulationEnded = false;
let endTime = 0;
let horizontalDelay = 2000; // 2000 milliseconds delay for horizontal alignment with P4
let finalNode = null; // To store the final node
let isPlaying = true; // To track if the simulation is playing
let speedFactor = 5; // Default speed factor

const voteColors = {
  'block': '#ff9aa2',    // Pastel red
  'vote': '#ffb7b2',    // Pastel orange
  'qc': '#ffdac1',    // Pastel yellow
  550: '#e2f0cb'     // Pastel green
};

class Node {
  constructor(x, y, label, startDelay,type) {
    this.x = x;
    this.y = y;
    this.label = label;
    this.sent = false;
    this.stage = 0; // Nodes are always at stage 0
    this.startDelay = startDelay;
    this.startTime = millis();
    this.type = type
  }

  draw() {
    fill('#c06c84');
    stroke('#c06c84');
    strokeWeight(2);
    ellipse(this.x, this.y, 50, 50);
    fill('#ffffff'); // White color for text
    noStroke();
    textAlign(CENTER, CENTER);
    text(this.label, this.x, this.y);
  }

  sendTraits() {
    if (!this.sent && millis() - this.startTime >= this.startDelay) {
      for (let point of points) {
        if (point.stage === 1 && this.y !== point.y) {
          let trait = new Trait(this.x, this.y, point.x, point.y, 0, voteColors[this.type]);
          
          // Add delay if horizontally aligned with P4
          if (this.y === 550) {
            setTimeout(() => traits.push(trait), horizontalDelay);
          } else {
            traits.push(trait);
          }
        }
      }
      this.sent = true;
    }
  }
}

class Point {
  constructor(x, y, stage,type) {
    this.x = x;
    this.y = y;
    this.received = 0;
    this.stage = stage;
    this.sent = false;
    this.color = '#355c7d'; // Default pastel color for points
    this.type = type
  }

  draw() {
    stroke(this.color);
    strokeWeight(10);
    fill(this.color);
    ellipse(this.x, this.y, 20, 20);
  }

  sendTraits() {
    let requiredReceived = (this.stage === 3 || this.stage === 5) ? 2 : 1;

    if (this.received >= requiredReceived && !this.sent) {
      for (let point of points) {
        if (this.stage + 1 === point.stage && this.y !== point.y) {
          let trait = new Trait(this.x, this.y, point.x, point.y, 0, voteColors[this.type]);
          
          // Add delay if horizontally aligned with P4
          if (this.y === 550) {
            setTimeout(() => traits.push(trait), horizontalDelay);
          } else {
            traits.push(trait);
          }
        }
      }
      this.sent = true;
    }
  }

  receiveTrait(trait) {
/*     if (this.stage === 2 || this.stage === 4) { // Change color for Vote 1 and Vote 2 stages
      this.color = voteColors[this.y] || 'blue';
      trait.color = this.color;
    } */
    this.received++;
  }
}

class Trait {
  constructor(startX, startY, endX, endY, stepProgress, color) {
    this.startX = startX;
    this.startY = startY;
    this.endX = endX;
    this.endY = endY;
    this.stepProgress = stepProgress;
    this.color = color;
    this.arrived = false;
    this.speed = Math.random()*1 + 1; // Random speed between 1 and 3

  }

  draw() {
    stroke(this.color);
    strokeWeight(3);
    line(this.startX, this.startY, lerp(this.startX, this.endX, this.stepProgress), lerp(this.startY, this.endY, this.stepProgress));
    if (!this.arrived) {
      this.stepProgress += (this.speed / 10000*totalSteps) * (speedFactor / 10);
      if (this.stepProgress >= 1) {
        this.arrived = true;
        for (let point of points) {
          if (dist(this.endX, this.endY, point.x, point.y) < 1) {
            point.receiveTrait(this);
          }
        }
        // Check if simulation has ended
        if (traits.filter(trait => trait.arrived).length >= 57) {
          if (checkElectionStageCompleted()) {
            simulationEnded = true;
            endTime = millis();
          }
        }
      }
    } else {
      stroke(this.color);
      strokeWeight(3);
      line(this.startX, this.startY, this.endX, this.endY);
    }
  }

  checkArrival() {
    return this.arrived;
  }
}

function setup() {
  createCanvas(1000, 600);
  stageWidth = width / stages.length;
  initializeNodesAndPoints();
  // Event listener for play/stop button
  select('#playStopButton').mousePressed(togglePlayStop);
  // Event listener for speed slider
  select('#speedSlider').input(updateSpeed);
}

function draw() {
  if (isPlaying) {
    background(255, 255, 255, 50); // Semi-transparent background for trailing effect
    drawTimeStages();
    drawPoints();

    for (let node of nodes) {
      node.draw();
      node.sendTraits();
    }

    for (let point of points) {
      point.draw();
      point.sendTraits();
    }

    for (let trait of traits) {
      trait.draw();
    }

    if (simulationEnded) {
      if (!finalNode) {
        // Select a random node label (P1, P2, P3, P4)
        const labels = ['P1', 'P2', 'P3', 'P4'];
        const randomLabel = random(labels);
        // Create a new Node at the right of the canvas
        finalNode = new Node(width - 50, height / 2, randomLabel, 0);
        finalNode.color = 'green'; // Set color to green
      }
      // Draw the final node
      fill('green');
      ellipse(finalNode.x, finalNode.y, 50, 50);
      fill('#ffffff'); // White color for text
      noStroke();
      textAlign(CENTER, CENTER);
      text(finalNode.label, finalNode.x, finalNode.y);

      if (millis() - endTime >= restartTime) {
        initializeNodesAndPoints();
        simulationEnded = false;
        finalNode = null; // Reset the final node
      }
    }
  }
}

function drawTimeStages() {
  stroke('#c06c84');
  strokeWeight(2);
  for (let i = 1; i < stages.length; i++) {
    let x = i * stageWidth;
    for (let y = 0; y < height; y += 10) {
      line(x, y, x, y + 5);
    }
  }

  // Draw stage labels
  fill('#355c7d');
  noStroke();
  textAlign(CENTER, CENTER);
  for (let i = 0; i < stages.length; i++) {
    let x = i * stageWidth + stageWidth / 2;
    text(stages[i], x, 30);
  }
}

function drawPoints() {
  noStroke();
  for (let point of points) {
    fill(point.color);
    ellipse(point.x, point.y, 20, 20);
  }
}

function initializeNodesAndPoints() {
  nodes = [];
  points = [];
  traits = [];
  simulationEnded = false;

  nodes.push(new Node(stageWidth / 2, 100, 'P1', 0, 'block'));
  nodes.push(new Node(stageWidth / 2, 250, 'P2', 0, 'block'));
  nodes.push(new Node(stageWidth / 2, 400, 'P3', 0, 'block'));
  nodes.push(new Node(stageWidth / 2, 550, 'P4', 2000, 'block')); // Adding a delay of 2000 milliseconds for P4

  points.push(new Point(stageWidth * 1.5, 100, 1, 'vote'));
  points.push(new Point(stageWidth * 1.5, 250, 1, 'vote'));
  points.push(new Point(stageWidth * 1.5, 400, 1, 'vote'));
  points.push(new Point(stageWidth * 1.5, 550, 1, 'vote'));

  points.push(new Point(stageWidth * 2.5, 100, 2,'block'));
  points.push(new Point(stageWidth * 2.5, 250, 2,'block'));
  points.push(new Point(stageWidth * 2.5, 400, 2,'block'));
  points.push(new Point(stageWidth * 2.5, 550, 2,'block'));

  points.push(new Point(stageWidth * 3.5, 100, 3, 'qc'));
  points.push(new Point(stageWidth * 3.5, 250, 3, 'qc'));
  points.push(new Point(stageWidth * 3.5, 400, 3, 'qc'));
  points.push(new Point(stageWidth * 3.5, 550, 3, 'qc'));

  points.push(new Point(stageWidth * 4.5, 100, 4,'vote'));
  points.push(new Point(stageWidth * 4.5, 250, 4,'vote'));
  points.push(new Point(stageWidth * 4.5, 400, 4,'vote'));
  points.push(new Point(stageWidth * 4.5, 550, 4,'vote'));

  points.push(new Point(stageWidth * 5.5, 100, 5,'qc'));
  points.push(new Point(stageWidth * 5.5, 250, 5,'qc'));
  points.push(new Point(stageWidth * 5.5, 400, 5,'qc'));
  points.push(new Point(stageWidth * 5.5, 550, 5,'qc'));
}

function checkElectionStageCompleted() {
  return points.every(point => {
    if (point.stage === 5) {
      return point.received > 0;
    }
    return true;
  });
}

function togglePlayStop() {
  isPlaying = !isPlaying;
  select('#playStopButton').html(isPlaying ? 'Stop' : 'Play');
}

function updateSpeed() {
  speedFactor = select('#speedSlider').value();
}
