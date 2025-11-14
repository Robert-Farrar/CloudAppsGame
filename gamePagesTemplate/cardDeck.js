const cards = [
    //id, imgname, sign, color, value
[1,"images/cards/RedPlusZero.png",'+',"red",0],
[2,"images/cards/RedPlusOne.png",'+',"red",1],
[3,"images/cards/RedPlusTwo.png",'+',"red",2],
[4,"images/cards/RedPlusThree",'+',"red",3],
[5,"images/cards/RedPlusFour",'+',"red",4],
[6,"images/cards/RedPlusFive",'+',"red",5],
[7,"images/cards/RedPlusSix",'+',"red",6],
[8,"images/cards/RedPlusSeven",'+',"red",7],
[9,"images/cards/RedPlusEight",'+',"red",8],
[10,"images/cards/RedPlusNine",'+',"red",9],
[11,"images/cards/BluePlusZero",'+',"blue",0],
[12,"images/cards/BluePlusPlusOne",'+',"blue",1],
[13,"images/cards/BluePlusTwo",'+',"blue",2],
[14,"images/cards/BluePlusThree",'+',"blue",3],
[15,"images/cards/BluePlusFour",'+',"blue",4],
[16,"images/cards/BluePlusFive",'+',"blue",5],
[17,"images/cards/BluePlusSix",'+',"blue",6],
[18,"images/cards/BluePlusSeven",'+',"blue",7],
[19,"images/cards/BluePlusEight",'+',"blue",8],
[20,"images/cards/BluePlusNine",'+',"blue",9],
[21,"images/cards/GreenPlusZero",'+',"green",0],
[22,"images/cards/GreenPlusOne",'+',"green",1],
[23,"images/cards/GreenPlusTwo",'+',"green",2],
[24,"images/cards/GreenPlusThree",'+',"green",3],
[25,"images/cards/GreenPlusFour",'+',"green",4],
[26,"images/cards/GreenPlusFive",'+',"green",5],
[27,"images/cards/GreenPlusSix",'+',"green",6],
[28,"images/cards/GreenPlusSeven",'+',"green",7],
[29,"images/cards/GreenPlusEight",'+',"green",8],
[30,"images/cards/GreenPlusNine",'+',"green",9],

[31,"",'-',"red",0],
[32,"",'-',"red",1],
[33,"",'-',"red",2],
[34,"",'-',"red",3],
[35,"",'-',"red",4],
[36,"",'-',"red",5],
[37,"",'-',"red",6],
[38,"",'-',"red",7],
[39,"",'-',"red",8],
[40,"",'-',"red",9],
[41,"",'-',"blue",0],
[42,"",'-',"blue",1],
[43,"",'-',"blue",2],
[44,"",'-',"blue",3],
[45,"",'-',"blue",4],
[46,"",'-',"blue",5],
[47,"",'-',"blue",6],
[48,"",'-',"blue",7],
[49,"",'-',"blue",8],
[50,"",'-',"blue",9],
[51,"",'-',"green",0],
[52,"",'-',"green",1],
[53,"",'-',"green",2],
[54,"",'-',"green",3],
[55,"",'-',"green",4],
[56,"",'-',"green",5],
[57,"",'-',"green",6],
[58,"",'-',"green",7],
[59,"",'-',"green",8],
[60,"",'-',"green",9],

[61,"",'*',"red",0],
[62,"",'*',"red",1],
[63,"",'*',"red",2],
[64,"",'*',"red",3],
[65,"",'*',"red",4],
[66,"",'*',"red",5],
[67,"",'*',"red",6],
[68,"",'*',"red",7],
[69,"",'*',"red",8],
[70,"",'*',"red",9],
[71,"",'*',"blue",0],
[72,"",'*',"blue",1],
[73,"",'*',"blue",2],
[74,"",'*',"blue",3],
[75,"",'*',"blue",4],
[76,"",'*',"blue",5],
[77,"",'*',"blue",6],
[78,"",'*',"blue",7],
[79,"",'*',"blue",8],
[80,"",'*',"blue",9],
[81,"",'*',"green",0],
[82,"",'*',"green",1],
[83,"",'*',"green",2],
[84,"",'*',"green",3],
[85,"",'*',"green",4],
[86,"",'*',"green",5],
[87,"",'*',"green",6],
[88,"",'*',"green",7],
[89,"",'*',"green",8],
[90,"",'*',"green",9],

[92,"",'/',"red",1],
[93,"",'/',"red",2],
[94,"",'/',"red",3],
[95,"",'/',"red",4],
[96,"",'/',"red",5],
[97,"",'/',"red",6],
[98,"",'/',"red",7],
[99,"",'/',"red",8],
[100,"",'/',"red",9],
[102,"",'/',"blue",1],
[103,"",'/',"blue",2],
[104,"",'/',"blue",3],
[105,"",'/',"blue",4],
[106,"",'/',"blue",5],
[107,"",'/',"blue",6],
[108,"",'/',"blue",7],
[109,"",'/',"blue",8],
[110,"",'/',"blue",9],
[112,"",'/',"green",1],
[113,"",'/',"green",2],
[114,"",'/',"green",3],
[115,"",'/',"green",4],
[116,"",'/',"green",5],
[117,"",'/',"green",6],
[118,"",'/',"green",7],
[119,"",'/',"green",8],
[120,"",'/',"green",9]
];

/**
 * Look up a card by its numeric ID.
 * Returns an object { id, img, sign, color, value } or null if not found.
 * Accepts numbers or numeric strings.
 */
function getCardById(id) {
    const nid = Number(id);
    if (Number.isNaN(nid)) return null;
    const row = cards.find(c => Number(c[0]) === nid);
    if (!row) return null;
    return { id: row[0], img: row[1], sign: row[2], color: row[3], value: row[4] };
}

/**
 * Pick a random card from `cards`.
 * If `allowedIds` is provided (array of ids), selection is restricted to those ids.
 * Returns the same object shape as getCardById or null when none available.
 */
function getRandomCard(allowedIds) {
    let pool = cards;
    if (Array.isArray(allowedIds) && allowedIds.length) {
        const allowedSet = new Set(allowedIds.map(Number));
        pool = cards.filter(c => allowedSet.has(Number(c[0])));
    }
    if (!pool || pool.length === 0) return null;
    const idx = Math.floor(Math.random() * pool.length);
    const row = pool[idx];
    return { id: row[0], img: row[1], sign: row[2], color: row[3], value: row[4] };
}

// Expose helpers for use in browser console or other scripts
if (typeof window !== 'undefined') {
    window.getCardById = getCardById;
    window.getRandomCard = getRandomCard;
}

/* Usage examples (open the page in a browser and run in console):
     getCardById(5);           // returns card with id 5
     getRandomCard();          // returns a random card
     getRandomCard([1,2,3]);   // returns a random card from ids 1,2,3
*/

/**
 * Compare two cards (by id) for color and sign equality.
 * Returns an object: { idA, idB, cardA, cardB, sameColor, sameSign, matchBoth }
 * or null if either id is invalid / card not found.
 */
function compareCardsByColorAndSign(idA, idB) {
    const a = getCardById(idA);
    const b = getCardById(idB);
    if (!a || !b) return null;
    const sameColor = String(a.color) === String(b.color);
    const sameSign = String(a.sign) === String(b.sign);
    return {
        idA: a.id,
        idB: b.id,
        cardA: a,
        cardB: b,
        sameColor,
        sameSign,
        matchBoth: sameColor && sameSign
    };
}

if (typeof window !== 'undefined') {
    window.compareCardsByColorAndSign = compareCardsByColorAndSign;
}

/* Usage examples:
   compareCardsByColorAndSign(5, 15); // compare id 5 with id 15
   const res = compareCardsByColorAndSign(1, 31);
   if (res) console.log(res.sameColor, res.sameSign, res.matchBoth);
*/
