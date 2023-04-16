function userDefinedFunction(input1, input2)
{
    var arrayInput1=JSON.parse(input1);
    var arrayInput2=JSON.parse(input2);
    if (!Array.isArray(arrayInput1) || !Array.isArray(arrayInput2))
    {
        throw new Error("intput1 or input2 not an array string");
    }
    if (arrayInput1.length!=arrayInput2.length)
    {
        return 0;
    }
    const dotProduct = arrayInput1.reduce((acc, val, i) => acc + val * arrayInput2[i], 0);
    const magnitudeA = Math.sqrt(arrayInput1.reduce((acc, val) => acc + val ** 2, 0));
    const magnitudeB = Math.sqrt(arrayInput2.reduce((acc, val) => acc + val ** 2, 0));
    return dotProduct / (magnitudeA * magnitudeB);
}