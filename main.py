from ursina import *
from ursina.ursinamath import clamp
from math import radians, cos, sin, sqrt


app = Ursina()
window.title = 'AeroX Flight Simulator'
window.borderless = False
window.fullscreen = False
window.exit_button.visible = True
window.fps_counter.enabled = True

Sky()

# ── Ground — large enough to fly around Sydney for a while ───────────────────
# 1 unit ≈ 10 metres, so 10000 units = 100 km across
ground = Entity(
    model='plane',
    scale=(10000, 1, 10000),
    texture='assets/textures/sydney_satellite.jpg',
    texture_scale=(1, 1),
    position=(0, 0, 0),
    collider='box'
)

RUNWAY_HEADING = 340

# Runway 34L at YSSY: ~3900 m long, 45 m wide → 390 × 4.5 units
runway = Entity(
    model='plane',
    scale=(45, 1, 3900),
    color=color.black,
    position=(0, 0.5, 0),
    rotation_y=RUNWAY_HEADING,
    collider='box'
)

# ── Centerline ────────────────────────────────────────────────────────────────
for i in range(60):
    Entity(
        parent=runway,
        model='cube',
        scale=(0.02, 0.002, 0.015),
        color=color.white,
        position=(0, 0.001, -0.47 + i * 0.016)
    )

# ── Threshold bars ────────────────────────────────────────────────────────────
for i in range(6):
    for side in (-1, 1):
        Entity(
            parent=runway, model='cube',
            scale=(0.05, 0.002, 0.008),
            color=color.white,
            position=(side * (0.15 + i * 0.04), 0.001, -0.46)
        )
        Entity(
            parent=runway, model='cube',
            scale=(0.05, 0.002, 0.008),
            color=color.white,
            position=(side * (0.15 + i * 0.04), 0.001, 0.46)
        )

# ── Edge lights ───────────────────────────────────────────────────────────────
for i in range(60):
    Entity(parent=runway, model='sphere', scale=0.008, color=color.white,
           position=(-0.49, 0.002, -0.47 + i * 0.016))
    Entity(parent=runway, model='sphere', scale=0.008, color=color.white,
           position=( 0.49, 0.002, -0.47 + i * 0.016))

# ── Threshold lights ──────────────────────────────────────────────────────────
for j in range(5):
    Entity(parent=runway, model='sphere', scale=0.01,
           color=color.rgb(0, 255, 0),
           position=(-0.4 + j * 0.2, 0.002, 0.49))
    Entity(parent=runway, model='sphere', scale=0.01,
           color=color.rgb(255, 0, 0),
           position=(-0.4 + j * 0.2, 0.002, -0.49))

# ── Plane — spawned at 34L threshold ─────────────────────────────────────────
# Scaled up to match: wingspan ~11 m = 1.1 units, length ~8 m = 0.8 units
plane = Entity(
    model='cube',
    color=color.white,
    scale=(11, 2, 8),          # wingspan, height, length in metres (units)
    position=(598, 1, -1644),  # 34L threshold world position
    rotation_y=RUNWAY_HEADING,
    collider='box'
)

# ── Flight physics constants ──────────────────────────────────────────────────
# Speed in units/frame.  1 unit = 10 m, target rotate speed ~70 m/s = 7 u/s
# at 60fps that's ~0.117 u/frame max
throttle          = 0.0
speed             = 0.0
GRAVITY           = 0.05        # units/frame downward acceleration
DRAG              = 0.0003
MAX_SPEED         = 0.25        # ~540 km/h top speed
THROTTLE_RATE     = 0.002
SPEED_RESPONSE    = 0.005
LIFT_COEFFICIENT  = 0.12
ROTATE_RATE       = 0.6         # degrees/frame at full input

cam_yaw       = 0.0
cam_pitch     = 25.0
cam_dist      = 40.0            # sit further back to see the bigger plane
CAM_SENSITIVITY = 80


def update():
    global throttle, speed, cam_yaw, cam_pitch

    if held_keys['w']:
        throttle += THROTTLE_RATE
    if held_keys['s']:
        throttle -= THROTTLE_RATE
    throttle = min(1, max(0, throttle))

    target_speed = throttle * MAX_SPEED
    speed += (target_speed - speed) * SPEED_RESPONSE

    pitch_input = (held_keys['up arrow'] - held_keys['down arrow']) * ROTATE_RATE
    roll_input  = (held_keys['right arrow'] - held_keys['left arrow']) * ROTATE_RATE

    plane.rotate(Vec3(pitch_input, 0, 0), relative_to=plane)
    plane.rotate(Vec3(0, 0, roll_input),  relative_to=plane)

    aoa = radians(plane.rotation_x)
    lift = speed * max(0, 1 - abs(aoa) * 0.3) * LIFT_COEFFICIENT
    vertical_velocity = lift - GRAVITY

    hit_info = raycast(plane.world_position, Vec3(0, -1, 0), distance=5, ignore=(plane,))
    if hit_info.hit and vertical_velocity < 0:
        plane.y = hit_info.world_point.y + 1.5
        vertical_velocity = 0
    else:
        plane.y += vertical_velocity

    speed = max(0, speed - DRAG)
    plane.position += plane.forward * speed

    # ── Orbit cam ─────────────────────────────────────────────────────────────
    if mouse.right:
        cam_yaw   += mouse.velocity[0] * CAM_SENSITIVITY
        cam_pitch -= mouse.velocity[1] * CAM_SENSITIVITY
        cam_pitch  = clamp(cam_pitch, -10, 80)

    yaw_rad   = radians(cam_yaw)
    pitch_rad = radians(cam_pitch)

    base_forward = plane.forward
    base_right   = plane.right

    ox = cos(yaw_rad) * (-base_forward.x) + sin(yaw_rad) * base_right.x
    oz = cos(yaw_rad) * (-base_forward.z) + sin(yaw_rad) * base_right.z

    horiz_len = sqrt(ox*ox + oz*oz)
    final_x = ox * cos(pitch_rad)
    final_y = horiz_len * sin(pitch_rad)
    final_z = oz * cos(pitch_rad)

    offset = Vec3(final_x, final_y, final_z).normalized() * cam_dist

    camera.position = plane.position + offset
    camera.look_at(plane.position + Vec3(0, 2, 0))


if __name__ == '__main__':
    app.run()