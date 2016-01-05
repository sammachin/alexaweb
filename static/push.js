function push(){
	var xhr = new XMLHttpRequest();
	xhr.open('GET', '/pushevent', true);
	xhr.onload = function(evt){
		console.log(xhr.response);
	}
	xhr.send();
	console.log("Sending....");
}
