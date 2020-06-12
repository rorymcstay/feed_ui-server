  // jQuerySG is the alias for jQuery that SelectorGadget uses:
  jQuerySG(document).ready(function() {
    console.log("Hello world");
    // whenever SelectorGadget makes a prediction, it will call this
    // function; customize to do whatever you want with it, such as
    // putting the CSS selector into your code editor
    window.sg_prediction = function(prediction) {
      console.log("sending message to parent with prediction: ", prediction);
      window.parent.postMessage({predicted: prediction}, 'http://localhost:3000');
    }
      SelectorGadget.toggle(); // to turn on SelectorGadget, call this method
                               // call it again to turn off the SelectorGadget
  });

