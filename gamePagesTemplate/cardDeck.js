const cards = [
    //id, imgname, sign, color, value
[1,"images/cards/RedPlusZero.png",'+',"red",0],
[2,"images/cards/RedPlusOne.png",'+',"red",1],
[3,"images/cards/RedPlusTwo.png",'+',"red",2],
[4,"images/cards/RedPlusThree.png",'+',"red",3],
[5,"images/cards/RedPlusFour.png",'+',"red",4],
[6,"images/cards/RedPlusFive.png",'+',"red",5],
[7,"images/cards/RedPlusSix.png",'+',"red",6],
[8,"images/cards/RedPlusSeven.png",'+',"red",7],
[9,"images/cards/RedPlusEight.png",'+',"red",8],
[10,"images/cards/RedPlusNine.png",'+',"red",9],
[11,"images/cards/BluePlusZero.png",'+',"blue",0],
[12,"images/cards/BluePlusOne.png",'+',"blue",1],
[13,"images/cards/BluePlusTwo.png",'+',"blue",2],
[14,"images/cards/BluePlusThree.png",'+',"blue",3],
[15,"images/cards/BluePlusFour.png",'+',"blue",4],
[16,"images/cards/BluePlusFive.png",'+',"blue",5],
[17,"images/cards/BluePlusSix.png",'+',"blue",6],
[18,"images/cards/BluePlusSeven.png",'+',"blue",7],
[19,"images/cards/BluePlusEight.png",'+',"blue",8],
[20,"images/cards/BluePlusNine.png",'+',"blue",9],
[21,"images/cards/GreenPlusZero.png",'+',"green",0],
[22,"images/cards/GreenPlusOne.png",'+',"green",1],
[23,"images/cards/GreenPlusTwo.png",'+',"green",2],
[24,"images/cards/GreenPlusThree.png",'+',"green",3],
[25,"images/cards/GreenPlusFour.png",'+',"green",4],
[26,"images/cards/GreenPlusFive.png",'+',"green",5],
[27,"images/cards/GreenPlusSix.png",'+',"green",6],
[28,"images/cards/GreenPlusSeven.png",'+',"green",7],
[29,"images/cards/GreenPlusEight.png",'+',"green",8],
[30,"images/cards/GreenPlusNine.png",'+',"green",9],

[31,"images/cards/RedMinusZero.png",'-',"red",0],
[32,"images/cards/RedMinusOne.png",'-',"red",1],
[33,"images/cards/RedMinusTwo.png",'-',"red",2],
[34,"images/cards/RedMinusThree.png",'-',"red",3],
[35,"images/cards/RedMinusFour.png",'-',"red",4],
[36,"images/cards/RedMinusFive.png",'-',"red",5],
[37,"images/cards/RedMinusSix.png",'-',"red",6],
[38,"images/cards/RedMinusSeven.png",'-',"red",7],
[39,"images/cards/RedMinusEight.png",'-',"red",8],
[40,"images/cards/RedMinusNine.png",'-',"red",9],
[41,"images/cards/BlueMinusZero.png",'-',"blue",0],
[42,"images/cards/BlueMinusOne.png",'-',"blue",1],
[43,"images/cards/BlueMinusTwo.png",'-',"blue",2],
[44,"images/cards/BlueMinusThree.png",'-',"blue",3],
[45,"images/cards/BlueMinusFour.png",'-',"blue",4],
[46,"images/cards/BlueMinusFive.png",'-',"blue",5],
[47,"images/cards/BlueMinusSix.png",'-',"blue",6],
[48,"images/cards/BlueMinusSeven.png",'-',"blue",7],
[49,"images/cards/BlueMinusEight.png",'-',"blue",8],
[50,"images/cards/BlueMinusNine.png",'-',"blue",9],
[51,"images/cards/GreenMinusZero.png",'-',"green",0],
[52,"images/cards/GreenMinusOne.png",'-',"green",1],
[53,"images/cards/GreenMinusTwo.png",'-',"green",2],
[54,"images/cards/GreenMinusThree.png",'-',"green",3],
[55,"images/cards/GreenMinusFour.png",'-',"green",4],
[56,"images/cards/GreenMinusFive.png",'-',"green",5],
[57,"images/cards/GreenMinusSix.png",'-',"green",6],
[58,"images/cards/GreenMinusSeven.png",'-',"green",7],
[59,"images/cards/GreenMinusEight.png",'-',"green",8],
[60,"images/cards/GreenMinusNine.png",'-',"green",9],

[61,"images/cards/RedMultiZero.png",'*',"red",0],
[62,"images/cards/RedMultiOne.png",'*',"red",1],
[63,"images/cards/RedMultiTwo.png",'*',"red",2],
[64,"images/cards/RedMultiThree.png",'*',"red",3],
[65,"images/cards/RedMultiFour.png",'*',"red",4],
[66,"images/cards/RedMultiFive.png",'*',"red",5],
[67,"images/cards/RedMultiSix.png",'*',"red",6],
[68,"images/cards/RedMultiSeven.png",'*',"red",7],
[69,"images/cards/RedMultiEight.png",'*',"red",8],
[70,"images/cards/RedMultiNine.png",'*',"red",9],
[71,"images/cards/BlueMultiZero.png",'*',"blue",0],
[72,"images/cards/BlueMultiOne.png",'*',"blue",1],
[73,"images/cards/BlueMultiTwo.png",'*',"blue",2],
[74,"images/cards/BlueMultiThree.png",'*',"blue",3],
[75,"images/cards/BlueMultiFour.png",'*',"blue",4],
[76,"images/cards/BlueMultiFive.png",'*',"blue",5],
[77,"images/cards/BlueMultiSix.png",'*',"blue",6],
[78,"images/cards/BlueMultiSeven.png",'*',"blue",7],
[79,"images/cards/BlueMultiEight.png",'*',"blue",8],
[80,"images/cards/BlueMultiNine.png",'*',"blue",9],
[81,"images/cards/GreenMultiZero.png",'*',"green",0],
[82,"images/cards/GreenMultiOne.png",'*',"green",1],
[83,"images/cards/GreenMultiTwo.png",'*',"green",2],
[84,"images/cards/GreenMultiThree.png",'*',"green",3],
[85,"images/cards/GreenMultiFour.png",'*',"green",4],
[86,"images/cards/GreenMultiFive.png",'*',"green",5],
[87,"images/cards/GreenMultiSix.png",'*',"green",6],
[88,"images/cards/GreenMultiSeven.png",'*',"green",7],
[89,"images/cards/GreenMultiEight.png",'*',"green",8],
[90,"images/cards/GreenMultiNine.png",'*',"green",9],

[92,"images/cards/RedDivOne.png",'/',"red",1],
[93,"images/cards/RedDivTwo.png",'/',"red",2],
[94,"images/cards/RedDivThree.png",'/',"red",3],
[95,"images/cards/RedDivFour.png",'/',"red",4],
[96,"images/cards/RedDivFive.png",'/',"red",5],
[97,"images/cards/RedDivSix.png",'/',"red",6],
[98,"images/cards/RedDivSeven.png",'/',"red",7],
[99,"images/cards/RedDivEight.png",'/',"red",8],
[100,"images/cards/RedDivNine.png",'/',"red",9],
[102,"images/cards/BlueDivOne.png",'/',"blue",1],
[103,"images/cards/BlueDivTwo.png",'/',"blue",2],
[104,"images/cards/BlueDivThree.png",'/',"blue",3],
[105,"images/cards/BlueDivFour.png",'/',"blue",4],
[106,"images/cards/BlueDivFive.png",'/',"blue",5],
[107,"images/cards/BlueDivSix.png",'/',"blue",6],
[108,"images/cards/BlueDivSeven.png",'/',"blue",7],
[109,"images/cards/BlueDivEight.png",'/',"blue",8],
[110,"images/cards/BlueDivNine.png",'/',"blue",9],
[112,"images/cards/GreenDivOne.png",'/',"green",1],
[113,"images/cards/GreenDivTwo.png",'/',"green",2],
[114,"images/cards/GreenDivThree.png",'/',"green",3],
[115,"images/cards/GreenDivFour.png",'/',"green",4],
[116,"images/cards/GreenDivFive.png",'/',"green",5],
[117,"images/cards/GreenDivSix.png",'/',"green",6],
[118,"images/cards/GreenDivSeven.png",'/',"green",7],
[119,"images/cards/GreenDivEight.png",'/',"green",8],
[120,"images/cards/GreenDivNine.png",'/',"green",9]
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
