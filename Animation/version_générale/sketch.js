let nodes = [];
let points = [];
let stages = ['Nodes', 'Block 1', 'Vote 1', 'Block 2', 'Vote 2', 'Election'];
let stageWidth;
let totalSteps = 120; // Nombre de frames pour compléter une étape
let traits = [];
let restartTime = 6000; // 6 secondes
let simulationEnded = false;
let endTime = 0;

const voteColors = {
  100: '#FFB6C1',   // LightPink
  250: '#ADD8E6',   // LightBlue
  400: '#90EE90',   // LightGreen
  550: '#FFD700'    // LightYellow
};

class Node {
  constructor(x, y, label, startDelay) {
    this.x = x;
    this.y = y;
    this.label = label;
    this.sent = false;
    this.stage = 0; // Nœuds toujours au stage 0
    this.startDelay = startDelay;
    this.startTime = millis();
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
          let trait = new Trait(this.x, this.y, point.x, point.y, 0, '#CCCCCC'); // Couleur pastel pour le trait
          traits.push(trait);
        }
      }
      this.sent = true;
    }
  }
}

class Point {
  constructor(x, y, label, stage) {
    this.x = x;
    this.y = y;
    this.label = label;
    this.received = 0;
    this.stage = stage;
    this.sent = false;
    this.color = '#CCCCCC'; // Couleur pastel par défaut pour les cercles
  }

  draw() {
    stroke(this.color);
    fill(255);
    ellipse(this.x, this.y, 50, 50);
    fill(0);
    noStroke();
    textAlign(CENTER, CENTER);
    text(this.label, this.x, this.y);
  }

  sendTraits() {
    let requiredReceived = (this.stage === 3 || this.stage === 5) ? 3 : 1;

    if (this.received >= requiredReceived && !this.sent) {
      for (let point of points) {
        if (this.stage + 1 === point.stage && this.y !== point.y) {
          let trait = new Trait(this.x, this.y, point.x, point.y, 0, '#CCCCCC'); // Couleur pastel pour le trait
          traits.push(trait);
        }
      }
      this.sent = true;
    }
  }

  receiveTrait(trait) {
    if (this.stage === 2 || this.stage === 4) { // Changement de couleur pour Vote 1 et Vote 2
      this.color = voteColors[this.y] || '#CCCCCC'; // Utilisation de la couleur associée
      trait.color = this.color;
    }
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
    this.speed = Math.floor(Math.random() * 3) + 1; // Vitesse aléatoire entre 1 et 3
  }

  draw() {
    stroke(this.color);
    strokeWeight(1);
    line(this.startX, this.startY, lerp(this.startX, this.endX, this.stepProgress), lerp(this.startY, this.endY, this.stepProgress));
    if (!this.arrived) {
      this.stepProgress += this.speed / (totalSteps * 2);
      if (this.stepProgress >= 1) {
        this.arrived = true;
        for (let point of points) {
          if (dist(this.endX, this.endY, point.x, point.y) < 1) {
            point.receiveTrait(this);
          }
        }
        // Vérification si la simulation est terminée
        if (traits.every(trait => trait.arrived)) {
          simulationEnded = true;
          endTime = millis();
        }
      }
    } else {
      stroke(this.color);
      strokeWeight(1);
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
  stroke('#CCCCCC'); // Couleur pastel pour les lignes de temps
  strokeWeight(2);
  for (let i = 1; i < stages.length; i++) {
    let x = i * stageWidth;
    for (let y = 0; y < height; y += 10) {
      line(x, y, x, y + 5);
    }
  }

  // Dessiner les étiquettes des étapes
  fill(0);
  noStroke();
  textAlign(CENTER, CENTER);
  for (let i = 0; i < stages.length; i++) {
    let x = i * stageWidth + stageWidth / 2;
    text(stages[i], x, 30);
  }
}

function drawPoints() {
  fill('#CCCCCC'); // Couleur pastel pour les cercles
  noStroke();
  for (let point of points) {
    for (let i = 1; i < stages.length; i++) {
      let x = i * stageWidth + stageWidth / 2;
      ellipse(x, point.y, 10, 10);
    }
  }
}

function initializeNodesAndPoints() {
  nodes = [];
  points = [];
  traits = [];
  simulationEnded = false;

  nodes.push(new Node(stageWidth / 2, 100, 'P1', 0));
  nodes.push(new Node(stageWidth / 2, 250, 'P2', 0));
  nodes.push(new Node(stageWidth / 2, 400, 'P3', 0));
  nodes.push(new Node(stageWidth / 2, 550, 'P4', 3000)); // Ajout d'un délai de 3000 millisecondes pour P4

  points.push(new Point(stageWidth * 1.5, 100, 'Q1', 1));
  points.push(new Point(stageWidth * 1.5, 250, 'Q2', 1));
  points.push(new Point(stageWidth * 1.5, 400, 'Q3', 1));
  points.push(new Point(stageWidth * 1.5, 550, 'Q4', 1));

  points.push(new Point(stageWidth * 2.5, 100, 'R1', 2));
  points.push(new Point(stageWidth * 2.5, 250, 'R2', 2));
  points.push(new Point(stageWidth * 2.5, 400, 'R3', 2));
  points.push(new Point(stageWidth * 2.5, 550, 'R4', 2));

  points.push(new Point(stageWidth * 3.5, 100, 'S1', 3));
  points.push(new Point(stageWidth * 3.5, 250, 'S2', 3));
  points.push(new Point(stageWidth * 3.5, 400, 'S3', 3));
  points.push(new Point(stageWidth * 3.5, 550, 'S4', 3));

  points.push(new Point(stageWidth * 4.5, 100, 'T1', 4));
  points.push(new Point(stageWidth * 4.5, 250, 'T2', 4));
  points.push(new Point(stageWidth * 4.5, 400, 'T3', 4));
  points.push(new Point(stageWidth * 4.5, 550, 'T4', 4));

  points.push(new Point(stageWidth * 5.5, 100, 'U1', 5));
  points.push(new Point(stageWidth * 5.5, 250, 'U2', 5));
  points.push(new Point(stageWidth * 5.5, 400, 'U3', 5));
  points.push(new Point(stageWidth * 5.5, 550, 'U4', 5));
}
