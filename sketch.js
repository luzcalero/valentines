// Particle settings
const PARTICLE_COUNT = 20000;
const NOISE_SCALE = 0.01;
const PARTICLE_SIZE = 3.5;
let particles = [];

// Curated colors from the original palette (names removed)
const PALETTE = [
    [255, 105, 180], [102, 51, 153], [144, 238, 144],
    [255, 218, 185], [221, 160, 221], [255, 160, 122],
    [176, 224, 230], [255, 192, 203], [221, 160, 221],
    [255, 0, 0], [238, 130, 238], [135, 206, 235],
    [255, 160, 122], [15, 82, 186], [173, 216, 230],
];

class Particle {
    constructor() {
        this.pos = createVector(random(width), random(height));
        this.color = random(PALETTE);
    }

    update() {
        let n = noise(this.pos.x * NOISE_SCALE, this.pos.y * NOISE_SCALE);
        let angle = TAU * n;
        this.pos.x += cos(angle);
        this.pos.y += sin(angle);

        if (!this.onScreen()) {
            this.pos.x = random(width);
            this.pos.y = random(height);
        }
    }

    show() {
        stroke(this.color[0], this.color[1], this.color[2], 50);
        strokeWeight(PARTICLE_SIZE);
        point(this.pos.x, this.pos.y);
    }

    onScreen() {
        return this.pos.x >= 0 && this.pos.x <= width &&
            this.pos.y >= 0 && this.pos.y <= height;
    }
}

function setup() {
    createCanvas(windowWidth, windowHeight);

    pixelDensity(1);
    frameRate(30);

    // Initialize particles
    particles = [];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
        particles[i] = new Particle();
    }

    background(0);
}

function draw() {
    background(0, 10);

    for (let particle of particles) {
        particle.update();
        particle.show();
    }
}

function windowResized() {
    resizeCanvas(windowWidth, windowHeight);
    background(0);
}


function mousePressed() {
    noiseSeed(millis());
}
