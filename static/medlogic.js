  let select=document.querySelector(".medicineNames");
  let para1=document.getElementById("para1");
  let para2=document.getElementById("para2");
  let para3=document.getElementById("para3");
  let para4=document.getElementById("para4");
  let para5=document.getElementById("para5");
  let paragraphs=document.querySelectorAll(".para");
for(let paragraph of paragraphs){
    if(paragraph.innerText.trim()===""){
    paragraph.innerText="Sorry No info on this part right now";
  }
}

 for(let med in medicines){
            let options=document.createElement("option")
            options.value=medicines[med];
            options.textContent=med;
            select.appendChild(options);
        }
select.addEventListener("change",(evt)=>{
        let medicine=evt.target.value;
        async function med(){
        if (medicine===""){
            alert("please enter a medicine name")
        }
        let response=await fetch(`https://api.fda.gov/drug/label.json?search=openfda.brand_name:${medicine}`);
        let data=await response.json();
        para1.innerText=data.results[0].indications_and_usage[0];
        para2.innerText=data.results[0].dosage_and_administration[0];
        para3.innerText=data.results[0].warnings[0];
        para4.innerText=data.results[0].do_not_use[0];
        para5.innerText=data.results[0].purpose[0];
        }
        med();
});
 