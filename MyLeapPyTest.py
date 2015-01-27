import os, sys, inspect, thread, time, uinput


import Leap
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture

device = uinput.Device([
        uinput.BTN_LEFT,
        uinput.BTN_RIGHT,
        uinput.REL_X,
        uinput.REL_Y,
        ])


class SampleListener(Leap.Listener):
	###################################User variables...changable########################################
	NumDragFin = 5
	NumDClickFin = 2
	NumRClickFin = 4
	NumPointFin = 1

	PrintCommands = 0

	ContiniousMouseSpeed = 9 #speed od continious mouse movement with finger (the smaller num, the faster movement)

	###################################Program variables...do not change!###############################
	Hand = 0
	Frame = 0
	start_frame=0

	OLDXpos = 0
	OLDYpos = 0
	NoTrackHandSphereRadius = 40 #closed hand is usually 30
	PointHandSphereRadius = 180 #max limit with which you only controll the mouse movement

	MouseClick = 0
	DragClicked = 0
	DubleClicked = 0
	RightClicked = 0
	SingleClicked = 0

	OLDFingersExtended = 0
	WaitBetweenCommandsCount = 0
	BetweenCommandsMaxCount = 20

	MaxJumpVal = 30 #max pixels crouser is allowed to jump on screen


	THUMB =	0 
	INDEX = 1 
	MIDDLE = 2
	RING = 3
	PINKY = 4


	def on_connect(self, controller):
		print "Connected"
		controller.enable_gesture(Leap.Gesture.TYPE_SWIPE);


	def on_frame(self, controller):
		frame = controller.frame()
		
		#if fingers have been detected
		if not frame.fingers.is_empty:
			#hand info:
			hand = frame.hands.rightmost
			hand_pointables = hand.pointables

			#make variables global
			self.Hand = hand 
			self.Frame = frame

			
			#stabilized_position = pointable.stabilized_tip_position
			

			extended_finger_list = frame.fingers.extended()
			FingersExtendedNum = len(extended_finger_list)

			index_fingers =hand.fingers.finger_type(self.INDEX)
			#print index_fingers

			#if only one finger is extended, move mouse
			if(FingersExtendedNum==self.NumPointFin or FingersExtendedNum ==self.NumDragFin):

				PointingFingerTipPos = extended_finger_list[0].stabilized_tip_position
				FingerTipVelocity = extended_finger_list[0].tip_velocity
	

				#here you can choose the stabilazed or non stabilazed hand positioning
				HandPosition = hand.stabilized_palm_position
				#HandPosition = hand.palm_position
				HandVelocity = hand.palm_velocity
				AvgHandVel = (abs(HandVelocity[0])+abs(HandVelocity[1])+abs(HandVelocity[2]))/3


				if(AvgHandVel>20 or self.DragClicked==1):
					self.Mouse(HandPosition, HandVelocity, 1)
				elif(AvgHandVel<=20):
					self.ContiniousMouse(HandPosition, PointingFingerTipPos)


				#reset clicks so you can click again
				self.DubleClicked = 0
				self.RightClicked = 0
				self.SingleClicked = 0


			#To avoid multiple commands per command
			if(self.WaitingBetweenCommands(FingersExtendedNum)==0):

				#duble click and avoid clicking continiously(DubleClicked)
				if(FingersExtendedNum == self.NumDClickFin and self.DubleClicked ==0):
					self.Click(1)
					#self.DubleClicked = 1

				#drag, avoid clicking multiple times per press(DragClicked)
				if(FingersExtendedNum ==self.NumDragFin and self.DragClicked ==0):
					self.Drag(1)
					self.DragClicked = 1
				#drop when finished dragging
				elif(FingersExtendedNum !=self.NumDragFin and self.DragClicked ==1):
					self.Drag(0)
					self.DragClicked = 0

				#Right click
				if(FingersExtendedNum == self.NumRClickFin and self.RightClicked ==0):
					self.RightClick()
					self.RightClicked = 1
				


	def Drag(self, Dragging):
		#drag
		if(Dragging ==1):
			device.emit(uinput.BTN_LEFT,1)
			
			if(self.PrintCommands==1):
				print "Drag ON"

		if(Dragging==0):
			device.emit(uinput.BTN_LEFT,0)
			
			if (self.PrintCommands==1):
				print "Drag OFF"

	def Click(self, NumOfClicks):

		#duble click
		if (NumOfClicks == 2):
			device.emit(uinput.BTN_LEFT,1)
			device.emit(uinput.BTN_LEFT,0)
			device.emit(uinput.BTN_LEFT,1)
			device.emit(uinput.BTN_LEFT,0)
			
			if(self.PrintCommands==1):
				print "Click Click"

		if(NumOfClicks == 1):
			#if you just entered remember th ebeginnig frame to reference the angle to
			if(self.SingleClicked == 0):
				self.start_frame = self.Frame
				self.SingleClicked = 2
			#print self.start_frame

			
			HandRotation = self.Hand.rotation_angle(self.start_frame, Leap.Vector.y_axis)
			print HandRotation  


	def RightClick(self):
		device.emit(uinput.BTN_RIGHT,1)
		device.emit(uinput.BTN_RIGHT,0)
		
		if(self.PrintCommands==1):
			print "RClick"

	def Mouse(self, Pos, Velocity, HighLowVelocity):
		Xpos = Pos[0]
		Ypos = Pos[1]
		#detect hand position
		if(Xpos!=0):
			Xpos = 280+Xpos
		Xpos = 280*2-Xpos


		#avoid making big jumps - adds smoothness
		if(abs(self.OLDYpos-Ypos)>self.MaxJumpVal or abs(self.OLDXpos-Xpos)>self.MaxJumpVal):
			self.OLDXpos = Xpos
			self.OLDYpos = Ypos


		ToYMove = self.OLDYpos-Ypos
		ToXMove = self.OLDXpos-Xpos

		self.OLDYpos = Ypos
		self.OLDXpos = Xpos

		#detect velocity and asume speed of cruzer
		#High velocity(hand)
		if (HighLowVelocity ==1):
			XVel = abs(Velocity[0]/30)
			YVel = abs(Velocity[1]/30)
		#Accurate movement-low velocity(finger)
		if(HighLowVelocity ==0):
			XVel = abs(Velocity[0]/100)
			YVel = abs(Velocity[1]/100)


		device.emit(uinput.REL_X, int(ToXMove*XVel))
		device.emit(uinput.REL_Y, int(ToYMove*YVel))

	def ContiniousMouse (self, HandPos, FingerPos):
		ToXMove = (HandPos[0]-FingerPos[0]-20)/self.ContiniousMouseSpeed
		ToYMove = (HandPos[1]-FingerPos[1])/self.ContiniousMouseSpeed

		#reverse x direction with (-1)
		device.emit(uinput.REL_X, int((-1)*ToXMove))
		device.emit(uinput.REL_Y, int(ToYMove))

	def WaitingBetweenCommands(self, FingersExtended):
		ToReturn = 1
		if(FingersExtended == self.OLDFingersExtended):
			self.WaitBetweenCommandsCount +=1
			if(self.WaitBetweenCommandsCount>=self.BetweenCommandsMaxCount):
				ToReturn = 0

		if(FingersExtended != self.OLDFingersExtended):
			self.WaitBetweenCommandsCount = 0

		self.OLDFingersExtended = FingersExtended

		return ToReturn






def main():
    # Create a sample listener and controller
    listener = SampleListener()
    controller = Leap.Controller()

    # Have the sample listener receive events from the controller
    controller.add_listener(listener)

    # Keep this process running until Enter is pressed
    print "Press Enter to quit..."
    try:
        sys.stdin.readline()
    except KeyboardInterrupt:
        pass
    finally:
        # Remove the sample listener when done
        controller.remove_listener(listener)


def main1():
	for i in range(100):
		time.sleep(0.1)
		device.emit(uinput.REL_X, i)
		device.emit(uinput.REL_Y, 5)


if __name__ == "__main__":
    main()

print "Clean exit"