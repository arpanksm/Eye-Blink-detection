
import numpy as np
import cv2
import time
import pygame
timer=0
closed_eye=False

#Initializing the face and eye cascade classifiers from xml files
face_cascade = cv2.CascadeClassifier("C:\\Users\\91947\\PycharmProjects\\pythonProject\\venv\\Lib\\site-packages\\cv2\\data\\haarcascade_frontalface_default.xml")
eye_cascade = cv2.CascadeClassifier("C:\\Users\\91947\\PycharmProjects\\pythonProject\\venv\\Lib\\site-packages\\cv2\\data\\haarcascade_eye_tree_eyeglasses.xml")
# face_cascade = cv2.CascadeClassifier("front_face.xml")
# eye_cascade = cv2.CascadeClassifier("eye_tree.xml")

#Variable store execution state
first_read = True

#Starting the video capture
cap = cv2.VideoCapture(0)
ret,img = cap.read()

# def alarm():
closed_eye=False
closed = False
timer = 0
# JUST PLAYING A VEICHLE START MUSIC TO DEMONSTRATE THAT HERE WE WILL HAVE A CODE THAT TURNS A MOTOR ENGINE ON
print("Starting the veichle\n")
pygame.init()

sound = pygame.mixer.Sound("C:\\Users\\91947\\Downloads\\carengine-5998.mp3")
sound.play()

pygame.time.wait(int(sound.get_length() * 1000))

pygame.quit()

while(ret):
    
	ret,img = cap.read()
	try:
	
	#Converting the recorded image to grayscale
		gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	#Applying filter to remove impurities
		gray = cv2.bilateralFilter(gray,5,1,1)
	except Exception as e:
		print("End of code")
	# except (Exception) as e:
	
	#Detecting the face for region of image to be fed to eye classifier
	faces = face_cascade.detectMultiScale(gray, 1.3, 5,minSize=(200,200))
	if(len(faces)>0):
		for (x,y,w,h) in faces:
			img = cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)

			#roi_face is face which is input to eye classifier
			roi_face = gray[y:y+h,x:x+w]
			roi_face_clr = img[y:y+h,x:x+w]
			eyes = eye_cascade.detectMultiScale(roi_face,1.3,5,minSize=(50,50))

			#Examining the length of eyes object for eyes
			if(len(eyes)>=2):
				#Check if program is running for detection
				if(first_read):
					closed_eye=False
					cv2.putText(img,
					"Eyes open!",
					(70,70),
					cv2.FONT_HERSHEY_PLAIN, 3,
					(255,255,255),2)
					timer=0
					
    				
				else:
					cv2.putText(img,
					"Eyes open!", (70,70),
					cv2.FONT_HERSHEY_PLAIN, 2,
					(255,255,255),2)
					

    	
			else:
				if(first_read):
					closed_eye=True
					
					cv2.putText(img,
					"Eyes closed", (70,70),
					cv2.FONT_HERSHEY_PLAIN, 3,
					(255,255,255),2)
					
					b=(time.time())
					
					timer+=1
					print((timer))
					if(timer>200 and timer <204):
						# PLAYING AN ALARM THRICE TO ALERT THE DRIVER

					
							
						pygame.init()

						sound = pygame.mixer.Sound("C:\\Users\\91947\\Downloads\\loud-beepy-alarm-81101.mp3")
						sound.play()

						pygame.time.wait(int(sound.get_length() * 1000))

						pygame.quit()
					elif(timer>204):
						print("stopping the veichle")
						# JUST PLAYING A VEICHLE START MUSIC TO DEMONSTRATE THAT HERE WE WILL HAVE A CODE THAT TURNS A MOTOR ENGINE OFF

						pygame.init()

						sound = pygame.mixer.Sound("C:\\Users\\91947\\Downloads\\cararriveandstop-6191.mp3")
						sound.play()

						pygame.time.wait(int(sound.get_length() * 1000))

						pygame.quit()
						# break
						cap.release()
						cv2.destroyAllWindows()
					
			
	else:
		cv2.putText(img,
		"No face detected",(100,100),
		cv2.FONT_HERSHEY_PLAIN, 3,
		(0,255,0),2)
		# timer+=1

	#Controlling the algorithm with keys
	cv2.imshow('img',img)
	a = cv2.waitKey(1)
	if(a==ord('q')):
		
		break
	elif(a==ord('s') and first_read):
		
    
		first_read = False

cap.release()
cv2.destroyAllWindows()