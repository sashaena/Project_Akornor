window.onload = function(){

	//welcome!
	console.log("Detect.js Loaded!");

	var canvas = document.getElementById('canvas');
	var context = canvas.getContext('2d');
	var video = document.getElementById('video');

	//var SOCKET_URL = "webS://echo.websocket.org";
	var SOCKET_URL = "ws://127.0.0.1:5000/webSocket";
	// live connection between client and server
	var webS = new WebSocket(SOCKET_URL);

	//setup socket
	webS.onopen = function(){
		webS.send("Open!");
	};
	webS.onclose = function(){
		console.log("Closed!");
	};
	webS.onmessage = function(event){
		console.log("Got message ", event);
	};
	webS.onerror = function(error){
		console.log("WebSocket Error ", error);
	};

	//add play event listener to the 'video' player
	// so far as the video event is playing, there is a set interval
	video.addEventListener('play', function(){
		setInterval(detectAndDraw, 2000);

	});

	if(navigator.mediaDevices && navigator.mediaDevices.getUserMedia){
		navigator.mediaDevices.getUserMedia({video: true}).then(function(stream){
			console.log("Starting webcam feed...");
			video.src = window.URL.createObjectURL(stream);
			video.play();

		});
	}else{
		console.log("Webcam not available")
	}

	// draws whatever is playing in the video on a canvas
	function detectAndDraw(){	
		context.drawImage(video, 0, 0, video.width, video.height);
		webS.send(canvas.toDataURL("image/jpeg"));
	}
}