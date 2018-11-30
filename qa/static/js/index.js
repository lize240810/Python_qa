//card-container-1
var cc1 = $('.card-container-1');
cc1.on('click',function(){
    var disappear = {
      top: '40px',
      opacity: '0'
    },
    appear={
      top:'0',
      opacity:'1'
    }
    var firstCard = cc1.children('.card').first();
  firstCard.css(disappear);
  var x = setTimeout(function(){
    //firstCard.remove();
    firstCard.css(appear);
    $('.card-container-1').append(firstCard);
  },200);
})

//card-container-2
var cc2 = $('.card-container-2');
cc2.children('.right').on('click',function(){
  var firstCard = $('.card-container-2 .card').first();
  cc2.children('.card-holder').append(firstCard);
});
cc2.children('.left').on('click',function(){
  var lastCard = $('.card-container-2 .card').last();
  cc2.children('.card-holder').prepend(lastCard);
});

//card-container-3
var cc3 = $('.card-container-3');
var cssLeft = {
      left: '20px',
      opacity: 0
    },
    cssRight = {
      left: '-20px',
      opacity: 0
    },
    cssReset = {
      right: 0,
      left: 0,
      opacity: 1
    };
cc3.children('.right').click(function(){
  var firstCard = $('.card-container-3 .card').first();
  firstCard.css(cssLeft);
  setTimeout(function(){
    cc3.append(firstCard);
    firstCard.css(cssReset);
  },300)
});
cc3.children('.left').click(function(){
  var lastCard = $('.card-container-3 .card').last();
  lastCard.css(cssRight);
  lastCard.insertAfter(cc3.children('.controller.left'));
  setTimeout(function(){
    lastCard.css(cssReset);
  },300)
});

var cc4 = $('.card-container-4');
cc4.children('.card').click(function(){
  cc4.prepend($(this));
})

var cc5 = $('.card-container-5');
cc5.click(function(){
  var firstCard = cc5.children('.card').first(),
      cssRoll = {
        transform: 'rotate(-45deg)',
        opacity:0
      };
  firstCard.css(cssRoll);
  setTimeout(function(){
    cc5.append(firstCard);
    firstCard.attr('style','');
  },300);
});

var cc6 = $('.card-container-6'),
    cssAppear = {
      opacity: 0
    }
cc6.children('.card').click(function(e){
  cc6.prepend($(this)); 
})