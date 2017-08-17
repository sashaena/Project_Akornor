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
		document.getElementById("onscreenClosed").innerHTML = "Please refresh page";
	};
	webS.onmessage = function(event){
		// The server sends the client a message with is passed as an event
		// Out of the event, there are different sections including the data
		console.log("Got message ", event);
		var data = JSON.parse(event.data);
		if(data.hasOwnProperty('error')){
			console.log("ERROR:", data.error);
			// document.getElementById("personName").innerHTML = data.error;
			// output.innerHTML
		}else{
			console.log("Found " + data.name);
			// output.innerHTML
			$('#myModal').modal();
			document.getElementById("personName").innerHTML = data.name;
			//src is always {hostname}/upload/{student_id}.jpg
			var imgUrl = "http://" + window.location.hostname + ":5000/upload/" + data.id + ".jpg";
			console.log(imgUrl);
			document.getElementById("showing").src = imgUrl;	
		}
		//use event.data as output from server
	};

	webS.onerror = function(error){
		console.log("WebSocket Error ", error);
		// if(error.hasOwnProperty('OSError'))
		// 	document.getElementById("onscreenError").innerHTML = onscreenError
		// }else{
		// 	return null
		// }
	};

	// document.querySelector('button').onclick = function(){
	// 	webS.send('Uploading in a giffy')
	// }
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