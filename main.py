from math import radians ,cos ,sin ,sqrt 
from ursina import *
from ursina .ursinamath import clamp 
import random 

app =Ursina ()
window .title ='AeroX Flight Simulator'
window .borderless =False 
window .fullscreen =False 
window .exit_button .visible =True 
window .fps_counter .enabled =True 

Sky ()

world =Entity ()
world .rotation =Vec3 (0 ,0 ,0 )

ground =Entity (
parent =world ,
model ='plane',
scale =(10000 ,1 ,10000 ),
texture ='assets/textures/sydney_satellite',
texture_scale =(1 ,1 ),
position =(0 ,0 ,0 ),
collider ='box'
)

RUNWAY_HEADING =340 

runway =Entity (
parent =world ,
model ='plane',
scale =(45 ,1 ,3900 ),
color =color .black ,
position =(0 ,0.5 ,0 ),
rotation_y =RUNWAY_HEADING ,
collider ='box'
)

for i in range (60 ):
    Entity (parent =runway ,model ='cube',scale =(0.02 ,0.002 ,0.015 ),
    color =color .white ,position =(0 ,0.005 ,-0.47 +i *0.016 ))

for i in range (6 ):
    for side in (-1 ,1 ):
        Entity (parent =runway ,model ='cube',scale =(0.05 ,0.002 ,0.008 ),
        color =color .white ,position =(side *(0.15 +i *0.04 ),0.001 ,-0.46 ))
        Entity (parent =runway ,model ='cube',scale =(0.05 ,0.002 ,0.008 ),
        color =color .white ,position =(side *(0.15 +i *0.04 ),0.001 ,0.46 ))

for i in range (60 ):
    Entity (parent =runway ,model ='sphere',scale =0.008 ,color =color .white ,
    position =(-0.49 ,0.002 ,-0.47 +i *0.016 ))
    Entity (parent =runway ,model ='sphere',scale =0.008 ,color =color .white ,
    position =(0.49 ,0.002 ,-0.47 +i *0.016 ))

for j in range (5 ):
    Entity (parent =runway ,model ='sphere',scale =0.01 ,color =color .rgb (0 ,255 ,0 ),
    position =(-0.4 +j *0.2 ,0.002 ,0.49 ))
    Entity (parent =runway ,model ='sphere',scale =0.01 ,color =color .rgb (255 ,0 ,0 ),
    position =(-0.4 +j *0.2 ,0.002 ,-0.49 ))

plane =Entity (
model ='cube',
color =color .white ,
scale =(11 ,2 ,8 ),
position =(0 ,2 ,0 ),
rotation_y =RUNWAY_HEADING ,
collider ='box'
)

throttle =0.0 
speed =0.0 
vertical_velocity =0.0 
on_ground =True 
pitch_rate =0.0 
roll_rate =0.0 
altitude =2.0 
touchdown_speed =0.0 

GRAVITY =0.012 
MAX_SPEED =0.35 
THROTTLE_RATE =0.005 
SPEED_RESPONSE =0.00095 
SPEED_DECAY =0.00008 
LIFT_COEFFICIENT =5.0 
STALL_ANGLE =20.0 
INDUCED_DRAG =0.00005 
BASE_DRAG =0.00005 
LIFTOFF_SPEED =0.02 
PITCH_INERTIA =0.16 
ROLL_INERTIA =0.12 
RATE_DECAY =0.88 
GROUND_FRICTION =0.0055 
GROUND_STEER_RATE =0.4 
GROUND_RUDDER_BLEND =0.35 
GROUND_PITCH_RATE =0.030 
GROUND_PITCH_LIMIT =-1.0 
LIFTOFF_PITCH =-0.05 
TAKEOFF_LIFT =0.00018 
GROUND_TAKEOFF_LIFT =0.00012 
RUDDER_RATE =0.14 
RUDDER_YAW_RATE =0.08 
AIRBORNE_LIFT_FACTOR =0.32 
GROUND_MAX_SPEED =0.247 
GROUND_ACCEL_SCALE =0.22 
GROUND_SPEED_RESPONSE =0.0006 
GROUND_TRANSITION_ALTITUDE =8.0 
GROUND_TRANSITION_DRAG_SCALE =1.8 
BRAKE_DECEL =0.00045 
SPOILER_DRAG =0.00018 
SPOILER_LIFT_PENALTY =0.22 
WIND_VECTOR =Vec3 (0.002 ,0 ,0.001 )
TURBULENCE_SCALE =0.0001 
STALL_SPEED_LOSS_BASE =0.0008 
STALL_SPEED_LOSS_VV =0.0003 
STALL_SPEED_LOSS_ALT =0.0000008 
STALL_SPEED_LOSS_SCALE =0.7 
TURN_COEFFICIENT =0.42 
cam_yaw =0.0 
cam_pitch =25.0 
cam_dist =40.0 
CAM_SENSITIVITY =80 
STALL_RECOVERY_HOLD =0.4 
STALL_RECOVERY_DOWN_SCALE =0.65 
STALL_RECOVERY_UP_SCALE =1.0 
stall_recovery_timer =0.0 

def make_hud_text (y_offset ):
    return Text (parent =camera .ui ,text ='',position =(-0.85 ,y_offset ),
    scale =1.4 ,color =color .lime ,font ='VeraMono.ttf')

def get_pitch_input (held_keys_state ):
    return (1 if held_keys_state ['up arrow']else 0 )-(1 if held_keys_state ['down arrow']else 0 )


def get_rudder_input (held_keys_state ):
    return (1 if held_keys_state .get ('d',False )or held_keys_state .get ('D',False )else 0 )-(1 if held_keys_state .get ('a',False )or held_keys_state .get ('A',False )else 0 )


txt_speed =make_hud_text (0.45 )
txt_altitude =make_hud_text (0.38 )
txt_vspeed =make_hud_text (0.31 )
txt_heading =make_hud_text (0.24 )
txt_throttle =make_hud_text (0.17 )
txt_aoa =make_hud_text (0.10 )
txt_stall =make_hud_text (0.03 )
txt_brake =make_hud_text (-0.04 )
txt_spoiler =make_hud_text (-0.11 )

stall_warning =Text (parent =camera .ui ,text ='',position =(0 ,0.1 ),
scale =3 ,color =color .red ,origin =(0 ,0 ))
bank_warning =Text (parent =camera .ui ,text ='',position =(0 ,0.0 ),
scale =3 ,color =color .orange ,origin =(0 ,0 ))

def update ():
    global throttle ,speed ,vertical_velocity ,on_ground 
    global pitch_rate ,roll_rate ,altitude ,cam_yaw ,cam_pitch ,bank_warning 
    global touchdown_speed ,stall_recovery_timer 

    if held_keys .get ('w',False )or held_keys .get ('W',False ):
        throttle +=THROTTLE_RATE 
    if held_keys .get ('s',False )or held_keys .get ('S',False ):
        throttle -=THROTTLE_RATE 
    throttle =clamp (throttle ,0.0 ,1.0 )

    spoilers_active =held_keys .get ('space',False )
    brake_input =held_keys .get ('b',False )or held_keys .get ('B',False )

    transition_factor =1.0 if on_ground else clamp ((GROUND_TRANSITION_ALTITUDE -altitude )/GROUND_TRANSITION_ALTITUDE ,0.0 ,1.0 )
    effective_max_speed =lerp (MAX_SPEED ,GROUND_MAX_SPEED ,transition_factor )
    effective_accel =lerp (1.0 ,GROUND_ACCEL_SCALE ,transition_factor )
    effective_decay =lerp (1.0 ,GROUND_TRANSITION_DRAG_SCALE ,transition_factor )

    if on_ground :
        target_speed =throttle *effective_max_speed 
    else :
        target_speed =min (throttle *MAX_SPEED ,effective_max_speed )

    if speed <target_speed :
        if on_ground :
            speed +=(target_speed -speed )*(0.01 *effective_accel )+GROUND_SPEED_RESPONSE 
        else :
            speed +=SPEED_RESPONSE *effective_accel 
    else :
        speed =max (target_speed ,speed -SPEED_DECAY *effective_decay )

    if on_ground and brake_input :
        brake_factor =0.25 +(1.0 -throttle )*0.45 
        speed =max (0 ,speed -BRAKE_DECEL *brake_factor )
    elif brake_input :
        speed =max (0 ,speed -BRAKE_DECEL *0.08 )

    if on_ground and spoilers_active :
        speed =max (0 ,speed -SPOILER_DRAG *1.2 )
    elif spoilers_active :
        speed =max (0 ,speed -SPOILER_DRAG *2.8 )

    speed =clamp (speed ,0.0 ,effective_max_speed )

    aoa_deg =-plane .rotation_x 
    aoa_rad =radians (aoa_deg )

    stalling =False 
    pitch_input =get_pitch_input (held_keys )
    rudder_input =get_rudder_input (held_keys )

    if on_ground :
        if speed >0.005 :
            steering_input =held_keys ['right arrow']-held_keys ['left arrow']
            steer =steering_input *GROUND_STEER_RATE 
            ground_rudder =(rudder_input +steering_input *GROUND_RUDDER_BLEND )*RUDDER_RATE 
            plane .rotation_y +=steer +ground_rudder 

        if pitch_input <0 :
            plane .rotation_x =max (plane .rotation_x -GROUND_PITCH_RATE ,GROUND_PITCH_LIMIT )
        else :
            plane .rotation_x =lerp (plane .rotation_x ,0.0 ,0.05 )

        plane .rotation_x =clamp (plane .rotation_x ,GROUND_PITCH_LIMIT ,0.0 )
        plane .rotation_z =lerp (plane .rotation_z ,0.0 ,0.08 )
        pitch_rate =0.0 
        roll_rate =0.0 

        if throttle ==0 :
            if speed >0.06 :
                speed =max (0 ,speed -GROUND_FRICTION *0.3 )
            else :
                speed =max (0 ,speed -GROUND_FRICTION *0.7 )

        if speed >=LIFTOFF_SPEED and plane .rotation_x <=LIFTOFF_PITCH and throttle >0.02 :
            pitch_factor =clamp ((-plane .rotation_x )/max (abs (LIFTOFF_PITCH ),1e-6 ),0.0 ,1.0 )
            lift_multiplier =1.05 +pitch_factor *0.8 
            target_lift =GROUND_TAKEOFF_LIFT *lift_multiplier 

            vertical_velocity =lerp (vertical_velocity ,vertical_velocity +target_lift ,0.02 )

    else :
        if aoa_deg <STALL_ANGLE :
            cl =max (0 ,sin (aoa_rad ))*LIFT_COEFFICIENT 
        else :
            stall_factor =max (0 ,1.0 -(aoa_deg -STALL_ANGLE )/25.0 )
            cl =max (0 ,LIFT_COEFFICIENT *stall_factor )
            stalling =True 

        if stalling or stall_recovery_timer >0 :
            stall_recovery_timer =max (stall_recovery_timer ,STALL_RECOVERY_HOLD )
            if pitch_input >0 :
                pitch_rate +=pitch_input *PITCH_INERTIA *STALL_RECOVERY_DOWN_SCALE 
            else :
                pitch_rate +=pitch_input *PITCH_INERTIA *STALL_RECOVERY_UP_SCALE 
        else :
            pitch_rate +=pitch_input *PITCH_INERTIA 

        if held_keys ['left arrow']:
            roll_rate -=ROLL_INERTIA 
        if held_keys ['right arrow']:
            roll_rate +=ROLL_INERTIA 

        pitch_rate =clamp (pitch_rate ,-4.0 ,4.0 )
        roll_rate =clamp (roll_rate ,-4.0 ,4.0 )

        plane .rotate (Vec3 (pitch_rate ,0 ,0 ),relative_to =plane )
        plane .rotate (Vec3 (0 ,0 ,roll_rate ),relative_to =plane )

        pitch_rate *=RATE_DECAY 
        roll_rate *=RATE_DECAY 

        if aoa_deg <STALL_ANGLE :
            cl =max (0 ,sin (aoa_rad ))*LIFT_COEFFICIENT 
        else :
            stall_factor =max (0 ,1.0 -(aoa_deg -STALL_ANGLE )/25.0 )
            cl =max (0 ,LIFT_COEFFICIENT *stall_factor )
            stalling =True 

        bank_rad =radians (plane .rotation_z )
        yaw_rate =TURN_COEFFICIENT *cl *speed *sin (bank_rad )+rudder_input *RUDDER_YAW_RATE 
        plane .rotate (Vec3 (0 ,yaw_rate ,0 ),relative_to =plane )

        bank_angle =abs (plane .rotation_z )
        bank_lift_factor =cos (bank_rad )

        lift =speed *speed *cl *AIRBORNE_LIFT_FACTOR *bank_lift_factor 
        induced_drag =cl *cl *INDUCED_DRAG 

        nose_down =radians (max (0 ,-plane .rotation_x ))
        dive_boost =sin (nose_down )*0.00004 

        vertical_velocity +=lift -GRAVITY +dive_boost 
        vertical_velocity +=(random .random ()-0.5 )*2 *TURBULENCE_SCALE 
        vertical_velocity =clamp (vertical_velocity ,-0.8 ,0.28 )

        if stalling :
            vertical_velocity -=0.003 *(1.0 -stall_factor )
            pitch_rate +=0.05 
            stall_speed_loss =(STALL_SPEED_LOSS_BASE +max (0.0 ,vertical_velocity )*STALL_SPEED_LOSS_VV +altitude *STALL_SPEED_LOSS_ALT )
            stall_speed_loss *=1.0 +(1.0 -stall_factor )*STALL_SPEED_LOSS_SCALE 
            speed =max (0 ,speed -stall_speed_loss )
            stall_recovery_timer =STALL_RECOVERY_HOLD 

        if spoilers_active :
            induced_drag +=SPOILER_DRAG *1.8 
            lift *=max (0.0 ,1.0 -SPOILER_LIFT_PENALTY )
            speed =max (0 ,speed -SPOILER_DRAG *4.4 )

        if stall_recovery_timer >0 :
            stall_recovery_timer =max (0 ,stall_recovery_timer -time .dt )

        fall_limit =-0.8 -(bank_angle /90.0 )*1.2 
        vertical_velocity =clamp (vertical_velocity ,fall_limit ,0.6 )
        speed =max (0 ,speed -BASE_DRAG -induced_drag )

    fwd =plane .forward 
    world .x -=fwd .x *speed 
    world .z -=fwd .z *speed 
    if not on_ground :
        world .position -=WIND_VECTOR 

    world .rotation =Vec3 (0 ,0 ,0 )

    plane .y +=vertical_velocity 

    hit_info =raycast (plane .world_position ,Vec3 (0 ,-1 ,0 ),distance =6 ,ignore =(plane ,))
    if hit_info .hit :
        ground_y =hit_info .world_point .y +2.0 

        taking_off_intent =(speed >=LIFTOFF_SPEED and plane .rotation_x <0 and throttle >0.02 )or (vertical_velocity >0.0001 )

        if taking_off_intent and plane .y <=ground_y :
            plane .y =ground_y +0.06 
            on_ground =False 
            vertical_velocity =max (vertical_velocity ,0.002 )
        if plane .y <=ground_y and vertical_velocity <=0 and not taking_off_intent :
            touchdown_speed =abs (vertical_velocity )
            plane .y =ground_y 
            vertical_velocity =0.0 
            on_ground =True 
            if abs (pitch_input )<0.5 :
                plane .rotation_x =lerp (plane .rotation_x ,0.0 ,0.2 )
            plane .rotation_z =lerp (plane .rotation_z ,0.0 ,0.2 )
        else :

            on_ground =False 
    else :
        on_ground =False 

    altitude =plane .y 

    if mouse .right :
        cam_yaw +=mouse .velocity [0 ]*CAM_SENSITIVITY 
        cam_pitch -=mouse .velocity [1 ]*CAM_SENSITIVITY 
        cam_pitch =clamp (cam_pitch ,-10 ,80 )

    yaw_rad =radians (cam_yaw )
    pitch_rad =radians (cam_pitch )
    base_forward =plane .forward 
    base_right =plane .right 

    ox =cos (yaw_rad )*(-base_forward .x )+sin (yaw_rad )*base_right .x 
    oz =cos (yaw_rad )*(-base_forward .z )+sin (yaw_rad )*base_right .z 
    horiz_len =sqrt (ox *ox +oz *oz )

    offset =Vec3 (ox *cos (pitch_rad ),horiz_len *sin (pitch_rad ),oz *cos (pitch_rad )).normalized ()*cam_dist 
    camera .position =plane .world_position +offset 
    camera .look_at (plane .world_position +Vec3 (0 ,2 ,0 ))
    camera .rotation_z =0 

    knots =speed *1944 
    fpm =vertical_velocity *196.85 
    hdg =plane .rotation_y %360 

    txt_speed .text =f'SPD  {knots :5.1f} kts'
    txt_altitude .text =f'ALT  {altitude *3.281 :.0f} ft'
    txt_vspeed .text =f'V/S  {fpm :+.0f} fpm'
    txt_heading .text =f'HDG  {hdg :05.1f}'
    txt_throttle .text =f'THR  {int (throttle *100 ):3d}%'
    txt_aoa .text =f'AoA  {aoa_deg :+.1f}'

    if stalling :
        txt_stall .text ='STALL'
        stall_warning .text ='STALL'
    else :
        txt_stall .text =''
        stall_warning .text =''

    txt_brake .text ='BRAKES'if brake_input and on_ground else ''
    txt_spoiler .text ='SPOILERS'if spoilers_active else ''

if __name__ =='__main__':
    app .run ()