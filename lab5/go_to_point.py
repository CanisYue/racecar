#!/usr/bin/python

import rospy
import numpy as np
import math
import tf

from std_msgs.msg import Float32
from ackermann_msgs.msg import AckermannDriveStamped
from geometry_msgs.msg import PoseArray, Pose, PointStamped

class GoToPointNode():
'''
Tell baby robot car how to drive to a baselink point with PID control, 
regardless of original input Point's coordinate system

Input: PointStamped (geometry_msgs/PointStamped.msg), robot post and orientation
Output: AckermannDriveStamped (ackermann_msgs/AckermannDriveStamped.msg)

Queries:
Do we want to change the max steering angle?
Is there anything we still need to tune? Dunno what Bobby's done in the past.
Do we need to take in pose/quaternion 

Stretch goal:
Back-up if destination is unreachable? Brainstorm scenarios?

Need to figure out how to take in pose and quaternian or something like that

'''
	def __init__(self):
        # Initial Settings
        self.k_steer = 0.1
        self.kp=0.6*self.k
        self.ki=0
        self.kd=0
        self.max_steering_angle = 0.2
        self.max_speed=.5
        self.lastDistance=0
        self.lastTheta=0
        self.distanceI=0
        self.thetaI=0

		# Default Settings
		self.k = 0.8;	
		self.topic_input = "/some_input_topic_here"
		self.topic_output = "/vesc/ackermann_cmd_mux/input/nav"
        self.base_frame = "base_link"
        self.map_frame = "odom";

        # Param Settings
        self.kfactor = rospy.get_param('~k', self.k)
        self.topic_input = rospy.get_param('~topic_input', self.topic_input)
        self.topic_output = rospy.get_param('~topic_output', self.topic_output)
        self.base_frame = rospy.get_param('~base_frame', self.base_frame)
        self.map_frame = rospy.get_param('~map_frame', self.map_frame)

		# Pubs and Subs
		self.drive_pub = rospy.Publisher(self.topic_output, AckermannDriveStamped, queue_size=1)
        rospy.Subscriber(self.topic_input, PointStamped, self.drive_callback)

		self.listener = tf.TransformListener(True, rospy.Duration(10.0))

	def drive_callback(self, data):
		# Get point and transform into odom frame
        data.header.stamp = self.listener.getLatestCommonTime(self.map_frame,data.header.frame_id)
        dest = self.listener.transformPoint(self.map_frame, data)
        x = dest.x
        y = dest.y

        # Computer dist and theta
        distance = math.pow(math.pow(x,2) + math.pow(y,2),  0.5)
        theta = math.atan2(y,x)

        # Prepare to Publish Drive Msg
        msg = AckermannDriveStamped()
        msg.header.stamp = rospy.Time.now()
        msg.header.frame_id = "base_link"

        # if obj close enough, else 
        if x<=0.2:
            msg.drive.steering_angle=theta
            msg.drive.speed=0.3
        else:
            self.distanceI= self.distanceI+distance
            dp= self.kp * distance
            di= self.kd*(distance - self.lastDistance)
            dd= self.ki*(self.distanceI)
            self.lastDistance=distance
            msg.drive.speed= max(0.1,min(self.max_speed, dp+di+dd))

            self.thetaI=self.thetaI+theta
            tp= self.k_steer * theta
            ti= self.ki*(self.thetaI)
            td= self.kd* (theta-self.lastTheta)
            msg.drive.steering_angle= max(min(self.max_steering_angle,theta), -1*self.max_steering_angle)
            self.lastTheta=theta
        print (msg.drive.speed, msg.drive.steering_angle)
        self.drive_pub.publish(msg)

if __name__=="__main__":
    rospy.init_node("GoToPoint")
    node = GoToPointNode()
    rospy.spin()
