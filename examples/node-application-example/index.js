var express = require("express");
var app = express();

app.set("view engine", "ejs");

app.get("/", function (req, res) {
  var title = "Tools Used To Build The App";
  var tools = [
    { name: "NodeJs", description: "This is Node JS Description" },
    { name: "Express", description: "This is Express Description" },
    { name: "EJS", description: "This is EJS Description" },
  ];

  res.render("pages/index", {
    tools: tools,
    title: title,
  });
});

app.get("/about", function (req, res) {
  res.render("pages/about");
});

app.listen(3000);
console.log("Server is listening on port 3000");
