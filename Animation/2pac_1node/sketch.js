let nodes = [];
let points = [];
let stages = ['Nodes', 'Block 1', 'Vote 1', 'Block 2', 'Vote 2', 'Election'];
let stageWidth;
let totalSteps = 120; // Number of frames to complete one stage, increased for slower propagation
let traits = [];
let restartTime = 6000; // 6 seconds
let simulationEnded = false;
let endTime = 0;

const voteColors = {
  'qc': '#FFA07A',       // Light Salmon
  'vote': '#98FB98',     // Pale Green
  'block': '#ADD8E6',    // Light Blue
  'coinshare': '#FFD700' // Gold
};

class Node {
  constructor(x, y, label, startDelay, type) {
    this.x = x;
    this.y = y;
    this.label = label;
    this.sent = false;
    this.stage = 0; // Nodes are always at stage 0
    this.startDelay = startDelay;
    this.startTime = millis();
    this.type = type;
  }

  draw() {
    fill(0);
    ellipse(this.x, this.y, 50, 50);
    fill(255);
    textAlign(CENTER, CENTER);
    text(this.label, this.x, this.y);
  }

  sendTraits() {
    if (!this.sent && millis() - this.startTime >= this.startDelay) {
      for (let point of points) {
        if (point.stage === 1 && this.y !== point.y) {
          let trait = new Trait(this.x, this.y, point.x, point.y, 0, voteColors[this.type]);
          traits.push(trait);
        }
      }
      this.sent = true;
    }
  }
}

class Point {
  constructor(x, y, stage, type) {
    this.x = x;
    this.y = y;
    this.received = 0;
    this.stage = stage;
    this.sent = false;
    this.color = voteColors[type]; // Use vote type color
    this.type = type;
  }

  draw() {
    noStroke();
    fill(this.color);
    ellipse(this.x, this.y, 30, 30); // Increased size for points
  }

  sendTraits() {
    let requiredReceived = (this.stage === 3 || this.stage === 5) ? 2 : 1;

    if (this.received >= requiredReceived && !this.sent) {
      for (let point of points) {
        if (this.stage + 1 === point.stage && this.y !== point.y) {
          let trait = new Trait(this.x, this.y, point.x, point.y, 0, voteColors[this.type]);
          traits.push(trait);
        }
      }
      this.sent = true;
    }
  }

  receiveTrait(trait) {
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
    this.speed = Math.random() * 1 + 1; // Random speed between 1 and 2
  }

  draw() {
    strokeWeight(3); // Increased stroke weight for traits
    stroke(this.color);
    line(this.startX, this.startY, lerp(this.startX, this.endX, this.stepProgress), lerp(this.startY, this.endY, this.stepProgress));
    if (!this.arrived) {
      this.stepProgress += this.speed / (totalSteps * 3);
      if (this.stepProgress >= 1) {
        this.arrived = true;
        for (let point of points) {
          if (dist(this.endX, this.endY, point.x, point.y) < 1) {
            point.receiveTrait(this);
          }
        }
        // Check if simulation has ended
        if (traits.every(trait => trait.arrived)) {
          simulationEnded = true;
          endTime = millis();
        }
      }
    }
  }
}

function setup() {
  createCanvas(1000, 600);
  stageWidth = width / stages.length;
  initializeNodesAndPoints();
}

function draw() {
  background(255);
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
    if (millis() - endTime >= restartTime) {
      initializeNodesAndPoints();
      simulationEnded = false;
    }
  }
}

function drawTimeStages() {
  stroke('green');
  strokeWeight(2);
  for (let i = 1; i < stages.length; i++) {
    let x = i * stageWidth;
    for (let y = 0; y < height; y += 10) {
      line(x, y, x, y + 5);
    }
  }

  // Draw stage labels
  fill(0);
  noStroke();
  textAlign(CENTER, CENTER);
  for (let i = 0; i < stages.length; i++) {
    let x = i * stageWidth + stageWidth / 2;
    text(stages[i], x, 30);
  }
}

function drawPoints() {
  for (let point of points) {
    point.draw();
  }
}

function initializeNodesAndPoints() {
  nodes = [];
  points = [];
  traits = [];
  simulationEnded = false;

  nodes.push(new Node(stageWidth / 2, 100, 'P1', 0, 'block'));

  points.push(new Point(stageWidth * 1.5, 100, 1, 'vote'));
  points.push(new Point(stageWidth * 1.5, 250, 1, 'vote'));
  points.push(new Point(stageWidth * 1.5, 400, 1, 'vote'));
  points.push(new Point(stageWidth * 1.5, 550, 1, 'vote'));

  points.push(new Point(stageWidth * 2.5, 100, 2, 'block'));
  points.push(new Point(stageWidth * 2.5, 250, 2, 'block'));
  points.push(new Point(stageWidth * 2.5, 400, 2, 'block'));
  points.push(new Point(stageWidth * 2.5, 550, 2, 'block'));

  points.push(new Point(stageWidth * 3.5, 100, 3, 'qc'));
  points.push(new Point(stageWidth * 3.5, 250, 3, 'qc'));
  points.push(new Point(stageWidth * 3.5, 400, 3, 'qc'));
  points.push(new Point(stageWidth * 3.5, 550, 3, 'qc'));

  points.push(new Point(stageWidth * 4.5, 100, 4, 'vote'));
  points.push(new Point(stageWidth * 4.5, 250, 4, 'vote'));
  points.push(new Point(stageWidth * 4.5, 400, 4, 'vote'));
  points.push(new Point(stageWidth * 4.5, 550, 4, 'vote'));

  points.push(new Point(stageWidth * 5.5, 100, 5, 'coinshare'));
  points.push(new Point(stageWidth * 5.5, 250, 5, 'coinshare'));
  points.push(new Point(stageWidth * 5.5, 400, 5, 'coinshare'));
  points.push(new Point(stageWidth * 5.5, 550, 5, 'coinshare'));
}
