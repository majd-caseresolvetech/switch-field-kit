(() => {
 const home=document.querySelector('#kiwix_serve_taskbar_library_button');
 if(home){home.href='/';home.target='_top';const b=home.querySelector('button');if(b)b.textContent='FIELD KIT HOME';}
 if(location.pathname==='/kiwix/'&&!document.querySelector('#fieldkit-home')){const a=document.createElement('a');a.id='fieldkit-home';a.href='/#guides';a.target='_top';a.textContent='‹ FIELD KIT HOME';document.body.prepend(a);}
})();
